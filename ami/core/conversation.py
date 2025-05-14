"""Conversation management for AMI."""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union
from functools import cached_property
from datetime import datetime

from .config import Config
from .logger import Logger as LogBase

class IllegalConversationId(Exception):
    """Raised when a conversation ID already exists."""
    pass

class Conversation(LogBase):
    """
    Manages a conversation between human and AI with message history and persistence.
    
    The conversation is saved to a file in the conversations directory specified
    in the Config. The file name is the conversation ID (8 characters).
    """

    def __init__(self):
        """Initialize a fresh conversation."""
        self.id = str(uuid.uuid4())[:8]
        self.messages: List[Dict[str, str]] = []
        self.files: Dict[str, str] = {}  # key -> file path

        if (self.conversations_dir / f"{self.id}.json").exists():
            raise IllegalConversationId(f"Conversation ID {self.id} already exists")

    def __getitem__(self, key: Union[int, slice]) -> Union[Dict[str, str], List[Dict[str, str]]]:
        """Support indexing and slicing of messages."""
        if isinstance(key, int):
            return self.messages[key]
        elif isinstance(key, slice):
            return self.messages[key]
        else:
            raise TypeError("Invalid index type")

    @cached_property
    def conversations_dir(self) -> Path:
        """Get the directory where conversations are stored."""
        return Config().convos_dir

    @cached_property
    def file_path(self) -> Path:
        """Get the path to this conversation's file."""
        return self.conversations_dir / f"{self.id}.json"

    @cached_property
    def transcript(self):
        """ Return the transcription for the conversation """
        return self.messages.copy()

    @classmethod
    def from_filepath(cls, file_path: Union[str, Path]) -> 'Conversation':
        """Create a Conversation instance from a file path, sorting messages by timestamp."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Conversation file {file_path} does not exist")

        with open(file_path) as f:
            data = json.load(f)

        conv = cls()
        conv.id = data["id"]
        conv.messages = sorted(
            data["messages"],
            key=lambda x: datetime.strptime(x["timestamp"], "%Y.%m.%d-%H:%M:%S.%f")
        )
        conv.files = data.get("files", {})
        return conv

    @classmethod
    def from_dict(cls, data: Dict) -> 'Conversation':
        """Create a Conversation instance from dictionary format, sorting messages by timestamp."""
        conv = cls()
        conv.id = data["id"]
        conv.messages = sorted(
            data["messages"],
            key=lambda x: datetime.strptime(x["timestamp"], "%Y.%m.%d-%H:%M:%S.%f")
        )
        conv.files = data.get("files", {})
        return conv

    def to_dict(self) -> Dict:
        """Convert conversation to dictionary format."""
        return {
            "id": self.id,
            "messages": self.messages,
            "files": self.files
        }

    def save(self) -> None:
        """Save conversation to file."""
        with open(self.file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def add_message(self, text: str, role: str, **metadata) -> None:
        """Add a message to the conversation with timestamp."""
        timestamp = datetime.now().strftime("%Y.%m.%d-%H:%M:%S.%f")[:-3]
        message = {
            "role": role,
            "message": text,
            "timestamp": timestamp,
            **metadata
        }
        self.messages.append(message)
        self.save()

    def add_file(self, key: str, file_path: Union[str, Path]) -> None:
        """Add a file associated with this conversation."""
        self.files[key] = str(file_path)
        self.save()

    def is_empty(self) -> bool:
        """Check if the conversation has no messages."""
        return len(self.messages) == 0

    def get_last_speaker(self) -> Optional[str]:
        """Return the role of the last speaker or None if no messages."""
        if not self.messages:
            return None
        return self.messages[-1]["role"]

    def get_last_message(self, role: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Get the most recent message, optionally filtered by role."""
        if not self.messages:
            return None
        if role:
            for msg in reversed(self.messages):
                if msg["role"] == role:
                    return msg
            return None
        return self.messages[-1]

    def get_context(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation context for the AI, optionally limited to last N messages."""
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages
