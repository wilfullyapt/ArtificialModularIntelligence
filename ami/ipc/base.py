from logging import warning
import time
import traceback
from multiprocessing import Process, Queue
from functools import cached_property
from typing import Dict, Callable
from queue import Empty

from ..core import LogBase, Config, Logger
from .constants import ProcessType, EventType
from .manager import IPCEvent, IPCManager


def on_event(event: EventType):
    """Decorator to mark a method as an event handler.

    Args:
        event: The EventType this method handles
    """
    def decorator(func: Callable):
        func._event_trigger = event
        return func
    return decorator


class BaseIPC(LogBase):
    def __init__(self, ipc_manager: IPCManager, process_type: ProcessType):
        super().__init__()
        self.process_manager = ipc_manager
        self.process_type: ProcessType = process_type
        ipc_logs_name = f"{self.__module__}.{self.__class__.__name__}:BaseIPC"
        self.ipc_logs: Logger = Logger(Config().log_config)(ipc_logs_name)

    def get_queue(self, process_type: ProcessType) -> Queue:
        """ Route an IPC event to its target process's event queue """
        return self.process_manager.event_queues[process_type]

    def route_event(self, event: IPCEvent):
        """ Route an IPC event to its target process's event queue. """
        self.get_queue(event.target).put(event)

    @cached_property
    def event_handlers(self) -> Dict[EventType, Callable]:
        handlers = {}
        for attr_name in dir(self):
            if attr_name != 'event_handlers':
                try:
                    attr = getattr(self, attr_name)
                    if hasattr(attr, '_event_trigger'):
                        handlers[attr._event_trigger] = attr
                except:
                    pass
        return handlers

    def start_event_handler(self):
        """Start the event handling thread for true event-driven processing."""
        import threading
        
        def event_loop():
            while self._running:
                try:
                    # Blocking wait for events - truly event-driven!
                    event = self.get_queue(self.process_type).get(timeout=1.0)
                    if isinstance(event, IPCEvent):
                        self._handle_event(event)
                except Empty:
                    continue  # Timeout, check if still running
                except Exception as e:
                    tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                    self.ipc_logs.error(f"Error in event loop: {e}\nFull traceback:\n{tb_str}")
        
        self._event_thread = threading.Thread(target=event_loop, daemon=True)
        self._event_thread.start()
        self.ipc_logs.info("Event handler thread started")

    def _handle_event(self, event: IPCEvent):
        """Handle a single event with proper error isolation."""
        if event.type in self.event_handlers:
            try:
                callback = self.event_handlers[event.type]
                self.ipc_logs.debug(f"Handling {event.type} with {callback.__name__}")
                callback(event)
            except Exception as e:
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                self.ipc_logs.error(f"Error handling event {event.type}: {e}\nFull traceback:\n{tb_str}")
        else:
            self.ipc_logs.warning(f"Unhandled event type: {event.type}")

    def check_and_handle_incoming_ipc_event(self):
        """Legacy method - replaced by event thread. Remove when all processes updated."""
        pass

    def update_cache(self):
        """ Update local cache from shared data."""
#       self.local_cache.update(self.shared_data)
        pass

class ProcessIPC(BaseIPC, Process):
    def __init__(self, ipc_manager: IPCManager, process_type: ProcessType):
        BaseIPC.__init__(self, ipc_manager, process_type)
        Process.__init__(self)
        self._running = False

    def running(self, value: bool):
        self._running = value

    def setup(self):
        """Override in subclass for initialization"""
        pass

    def loop(self):
        """Override in subclass for main loop logic"""
        pass

    def run(self):
        """
        Event-driven process main loop - no more wasteful polling!
        """
        try:
            self.setup()
            self._running = True
            
            # Start dedicated event handling thread
            self.start_event_handler()
            
            # Main thread handles business logic
            while self._running:
                self.loop()  # Business logic loop
                time.sleep(0.1)  # Much less frequent for business logic
                
        except Exception as e:
            self.ipc_logs.error(f"Process run loop failed: {e}")
            self._running = False
        finally:
            self.cleanup()

    @on_event(EventType.GLOBAL_STOP)
    def stop(self, event: IPCEvent):
        self._running = False



