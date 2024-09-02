""" Headspace Dialog as used by GUI, AI, and Headspaces 

This module defines the Dialog class, which represents a conversation structure
used in various parts of the application, including GUI interactions, AI communications,
and Headspace functionalities.

The Dialog class includes properties for managing conversation history, thoughts,
visual elements, and other related attributes.
"""

from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field

class Dialog(BaseModel):
    """
    Represents a conversation structure used in GUI interactions, AI communications, and Headspace functionalities.

    Attributes:
        headspace (str): The headspace associated with the dialog.
        convo (List[tuple]): List of tuples describing the conversation history.
        thoughts (Optional[str]): Background thoughts of the AI or Agent.
        visual (Optional[Path]): Optional path to the visual to display.
        timeout (int): Timeout value for the dialog, default is 10.
        finished (bool): Indicates if the dialog is finished, default is True.

    The Dialog class manages conversation history, thoughts, visual elements, and other related attributes.
    It provides methods for accessing the conversation history and adding new entries to it.
    """
    headspace: str
    convo: List[tuple] = Field(default_factory=list, description="List of tuples describing the conversation history")
    thoughts: Optional[str] = Field(None, description="These are the background thoughts of the AI or the Agent")
    visual: Optional[Path] = Field(None, description="Optional path to the visual to display")
    timeout: int = 10
    finished: bool = True

    class Config:
        arbitrary_types_allowed=True

    @property
    def history(self):
        """ Histroy property for the convo member """
        history = [ f"{entity}: {message}" for (entity, message) in self.convo ]
        return "\n".join(history)

    def push(self, conversation_history: List[tuple]):
        """ Append to the conversation """
        self.convo.extend(conversation_history)
