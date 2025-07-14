"""
IPC (Inter-Process Communication) module using Python's multiprocessing library.
Replaces gRPC-based communication with native Python multiprocessing primitives.
"""

from .constants import ProcessType, EventType, StateType
from .manager import IPCManager, IPCEvent
from .base import BaseIPC, ProcessIPC, on_event
from .qt_widgets import IPCQWidget

__all__ = [
    'ProcessType',
    'EventType',
    'StateType',
    'BaseIPC',
    'ProcessIPC',
    'IPCManager',
    'IPCEvent',
    'on_event',
    'IPCQWidget',
]
