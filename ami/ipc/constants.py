"""Constants for IPC module."""
from enum import Enum

class ProcessType(Enum):
    """Types of processes in the system."""

    AI = "AI"
    GUI = "GUI"
    BACKEND = "BACKEND"
    SYSTEM = "SYSTEM"

class EventType(Enum):
    """Types of events that can be sent between processes."""

    HOTWORD_DETECTED = "HOTWORD_DETECTED"
    TRANSCRIPTION_READY = "TRANSCRIPTION_READY"
    RESPONSE_READY = "RESPONSE_READY"
    INTERACTION_COMPLETED = "INTERACTION_COMPLETED"
    ERROR = "ERROR"
    COMMAND = "COMMAND"
    STATE_CHANGE = "STATE_CHANGE"
    GLOBAL_STOP = "GLOBAL_STOP"
    WATCHDOG_EVENT = "WATCHDOG_EVENT"

    CONFIG_CHANGED = "CONFIG_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"
    PLUGIN_CHANGED = "PLUGIN_CHANGED"

    RELOAD_GUI = "RELOAD_GUI"

class StateType(Enum):
    """States for the AI system."""

    IDLE = "IDLE"
    WAITING = "WAITING"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
