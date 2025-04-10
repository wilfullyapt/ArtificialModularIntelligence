"""State management for the AI system"""
import asyncio
from enum import Enum
from typing import Optional

class AIState(Enum):
    STARTING_UP     = "STARTING_UP"         # AI State Machine init this state
    WAITING_HOTWORD = "WAITING_HOTWORD"     # Waiting for hotword detection
    LISTENING       = "LISTENING"           # Actively listening for speech
    PROCESSING      = "PROCESSING"          # Processing speech input
    RESPONDING      = "RESPONDED"           # Generating/playing response
    ERROR           = "ERROR"               # Error state

    @classmethod
    def from_string(cls, value: str):
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"'{value}' is not a valid AIState")

def format_stt_event(text):
    return { "event": AIState.PROCESSING.value, "message": text }

class AIStateMachine:
    """
    Finite State Machine for the AI system that manages transitions between states
    and notifies subscribers of state changes.
    """
    def __init__(self):
        """Initialize the state machine in WAITING state"""
        self.state = AIState.STARTING_UP
        self.state_queue = asyncio.Queue()
        self._transition_lock = asyncio.Lock()
        self._state_history = []

    @property
    def current_state(self) -> AIState:
        """Get the current state"""
        return self.state

    async def transition_to(self, new_state: AIState) -> bool:
        """
        Transition to a new state if valid and notify subscribers.

        Args:
            new_state (AIState): The state to transition to

        Returns:
            bool: True if transition was successful, False otherwise
        """
        async with self._transition_lock:
            if new_state != self.state:
                self._state_history.append(self.state)
                self.state = new_state
                await self.state_queue.put(new_state.value)
                return True
        return False

    async def revert_to_previous(self) -> Optional[AIState]:
        """
        Revert to the previous state if available.

        Returns:
            Optional[AIState]: The previous state if available, None otherwise
        """
        if self._state_history:
            previous_state = self._state_history.pop()
            await self.transition_to(previous_state)
            return previous_state
        return None

    def is_in_state(self, state: AIState) -> bool:
        """
        Check if the machine is in a specific state.

        Args:
            state (AIState): The state to check

        Returns:
            bool: True if in the specified state, False otherwise
        """
        return self.state == state
