"""Central IPC Manager that coordinates communication between processes."""

from functools import cached_property
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from queue import Empty
from multiprocessing import Event, Queue, Manager
from multiprocessing.synchronize import Event as mpEventType

from ..core import LogBase, Config
from ..core import PluginRegistry

from .constants import ProcessType, EventType, StateType

@dataclass
class IPCEvent:
    """Event data structure for IPC communication."""
    type: EventType
    source: ProcessType
    target: ProcessType
    data: Any = None

    def forward(self, new_target: ProcessType) -> "IPCEvent":
        """Create a new IPCEvent with updated target."""
        return IPCEvent(
            type=self.type,    # Using keyword args for clarity
            source=self.source,
            target=new_target,
            data=self.data
        )
class IPCManager(LogBase):
    """
    Central manager and broker for inter-process communication.
    Uses multiprocessing primitives to handle communication between processes.

    It's important to note here, this class is meant to be instanced in the main process.
    The manager is copied, when passed, to the forked processes. However, the multiprocessing
    primitives as member reference the same Manager, State, Queues, and Events between
    each process. Effectively this one object in each process faciliates communication
    between them.

    Attributes:
        manager (multiprocessing.Manager): Multiprocess Manager; Meat and Po-ta-toes
        state (multiprocessing.Value): Effectively the state of the app at any given time
        event_queues (multiprocessing.Queue): Pub/Sub style communications; State change stuff
        command_queues (multiprocessing.Queue): RPC; Request and Response style communication
        state_event (multiprocessing.Event): Manager state change flag
        _plugin_metadata (multiprocessing.dict): Shared JSON plugin metadata

    Methods:
        NO POINT. THIS WILL CHANGE

    """
    def __init__(self, stop_flag: Optional[mpEventType]=None):
        """Initialize the IPC Manager."""

        self._stop_flag = stop_flag
        self.manager = Manager()
        self.state = self.manager.Value('i', StateType.IDLE.value)
        self.event_queues: Dict[ProcessType, Queue] = {
            proc_type: Queue() for proc_type in ProcessType
        }
        self.command_queues: Dict[ProcessType, Queue] = {
            proc_type: Queue() for proc_type in ProcessType
        }
        self.state_event = Event()
        self._plugin_metadata = self.manager.dict()
        self._plugin_metadata.update(self.registry.to_dict())

        self._conversation = self.manager.dict()
        self._conversation.update({})

    @property
    def stop_flag(self):
        if self._stop_flag:
            return self._stop_flag
        raise ValueError(f"STOP_FLAG doesn't exist! Cannot continue!")

    def get_state(self) -> StateType:
        """Get current system state."""
        return StateType(self.state.value)

    def set_state(self, state: StateType):
        """Set system state and notify all processes."""
        self.state.value = state.value
        self.state_event.set()
        # Notify all processes of state change
        for proc_type in ProcessType:
            self.send_event(IPCEvent(
                type=EventType.STATE_CHANGE,
                source=ProcessType.AI,  # AI owns state
                target=proc_type,
                data=state
            ))

    def send_event(self, event: IPCEvent):
        """Send event to target process."""
        self.event_queues[event.target].put(event)

    def get_event(self, proc_type: ProcessType, timeout: Optional[float] = None) -> Optional[IPCEvent]:
        """Get next event for the specified process."""
        try:
            return self.event_queues[proc_type].get(timeout=timeout)
        except Empty:
            return None

    def send_command(self, source: ProcessType, target: ProcessType, command: Any):
        """Send command from source to target process."""
        self.command_queues[target].put((source, command))

    def get_command(self, proc_type: ProcessType, timeout: Optional[float] = None) -> Optional[tuple[ProcessType, Any]]:
        """Get next command for the specified process."""
        try:
            return self.command_queues[proc_type].get(timeout=timeout)
        except Empty:
            return None

    def wait_for_state_change(self, timeout: Optional[float] = None) -> bool:
        """Wait for state change event."""
        result = self.state_event.wait(timeout)
        if result:
            self.state_event.clear()
        return result

    @cached_property
    def registry(self) -> PluginRegistry:
        """Plugin registry instance."""
        return PluginRegistry(self)

    @property
    def conversation(self) -> Optional[Dict]:
        """Get the current conversation state."""
        return dict(self._conversation)

    def set_conversation(self, conversation_data: Dict) -> None:
        """Set the current conversation state."""
        self._conversation.update(conversation_data)
