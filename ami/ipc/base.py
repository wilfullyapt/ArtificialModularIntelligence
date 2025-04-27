import time
from multiprocessing import Process, Queue
from functools import cached_property
from typing import Dict, Callable
from queue import Empty

from ami.core import LogBase, Config, Logger
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
        ipc_logs_name = f"{self.__module__}.{self.__class__.__name__}.process"
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



    def check_and_handle_incoming_ipc_event(self):
        """
        Handle the incoming events in the proces specific multiprocessing Queue


        Events handling is specific to the `@on_event` decorator, which you can see in use in the ProcessIPC.run Keep Alive loop.
        """
        try:
            # Get the event from the queue and assert the instance it is
            event = self.get_queue(self.process_type).get_nowait()
            assert isinstance(event, IPCEvent)

            # If there is an EventType registered, execute it with this event
            if event.type in self.event_handlers:
                try:
                    callback = self.event_handlers[event.type]
                    self.ipc_logs.info(f"BaseIPC Event Handling {event.type}: {callback}")
                    self.event_handlers[event.type](event)
                except Exception as e:
                    self.ipc_logs.error(f"Error handling event {event.type}: {e}")

            else:
                self.ipc_logs.warning(f"Unhandled event type: {event.type}")

        except (AssertionError, Empty):
            pass
        except Exception as e:
            self.ipc_logs.error(f"Error in event loop: {e}")

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
        When the Process.start() function is called, this run function is what happens in the forked process in the main thread, which we intend to keep alive.
        We loop check the process specific queue and handle the event.
        """
        self.setup()
        self._running = True

        # Keep Alive loop
        while self._running:
            self.check_and_handle_incoming_ipc_event()
            self.loop()         # Run the subclassed loop function
            time.sleep(0.01)

    @on_event(EventType.GLOBAL_STOP)
    def stop(self, event: IPCEvent):
        self._running = False



