"""Constants for IPC module."""
from enum import Enum

class ProcessType(Enum):
    """Types of processes in the system."""

    AI = "AI"
    GUI = "GUI"
    BACKEND = "BACKEND"
    SYSTEM = "SYSTEM"

from enum import Enum, IntEnum

class EventPriority(IntEnum):
    """Event priority levels for queue processing."""
    CRITICAL = 0    # GLOBAL_STOP, ERROR
    HIGH = 1        # HOTWORD_DETECTED, TRANSCRIPTION_READY
    NORMAL = 2      # RESPONSE_READY, STATE_CHANGE
    LOW = 3         # CONFIG_CHANGED, PLUGIN_CHANGED

class EventType(Enum):
    """Types of events that can be sent between processes."""

    # High priority - real-time interaction
    HOTWORD_DETECTED = "HOTWORD_DETECTED"
    TRANSCRIPTION_READY = "TRANSCRIPTION_READY"
    RESPONSE_READY = "RESPONSE_READY"
    INTERACTION_COMPLETED = "INTERACTION_COMPLETED"
    INLINE_POPUP = "INLINE_POPUP"

    # Critical priority - system control
    ERROR = "ERROR"
    GLOBAL_STOP = "GLOBAL_STOP"
    
    # Normal priority - system state
    COMMAND = "COMMAND"
    STATE_CHANGE = "STATE_CHANGE"
    WATCHDOG_EVENT = "WATCHDOG_EVENT"
    
    # Low priority - configuration
    CONFIG_CHANGED = "CONFIG_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"
    PLUGIN_CHANGED = "PLUGIN_CHANGED"
    RELOAD_GUI = "RELOAD_GUI"
    
    @property
    def priority(self) -> EventPriority:
        """Get priority level for this event type."""
        high_priority = {
            self.HOTWORD_DETECTED, self.TRANSCRIPTION_READY,
            self.RESPONSE_READY, self.INTERACTION_COMPLETED
        }
        critical_priority = {self.ERROR, self.GLOBAL_STOP}
        low_priority = {
            self.CONFIG_CHANGED, self.METADATA_CHANGED, 
            self.PLUGIN_CHANGED, self.RELOAD_GUI
        }
        
        if self in critical_priority:
            return EventPriority.CRITICAL
        elif self in high_priority:
            return EventPriority.HIGH
        elif self in low_priority:
            return EventPriority.LOW
        else:
            return EventPriority.NORMAL

class StateType(Enum):
    """States for the AI system."""

    IDLE = "IDLE"
    WAITING = "WAITING"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
