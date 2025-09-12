"""
IPC (Inter-Process Communication) module using Python's multiprocessing library.
Replaces gRPC-based communication with native Python multiprocessing primitives.
"""

from .constants import ProcessType, EventType, StateType
from .manager import IPCManager, IPCEvent
from .base import BaseIPC, ProcessIPC, on_event
# Optional Qt widget import - only load if needed
def _import_qt_widgets():
    """Lazy import Qt widgets to avoid PyQt6 dependencies in headless environments"""
    try:
        from .qt_widgets import IPCQWidget
        return IPCQWidget
    except ImportError:
        # GUI dependencies not available
        return None

IPCQWidget = _import_qt_widgets()

__all__ = [
    'ProcessType',
    'EventType',
    'StateType',
    'BaseIPC',
    'ProcessIPC',
    'IPCManager',
    'IPCEvent',
    'on_event',
]

# Add Qt widget to __all__ if it was successfully imported
if IPCQWidget is not None:
    __all__.append('IPCQWidget')
