""" Main full screen UI for the AMI system """

import re
import traceback
from typing import Any, Dict, Tuple

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication

from ..core import PluginRegistry, PluginVertical
from ..ipc import IPCManager, ProcessType, EventType, IPCQWidget, IPCEvent, on_event

from .popup import AMIDialog
from .layouts import ManagedFlexiblePositioningLayout

def parse_colon_string(input_string: str) -> Tuple[str, str]:
    pattern = r'^([a-zA-Z]+):([a-zA-Z]+)$'
    match = re.match(pattern, input_string)
    if not match:
        raise ValueError(f"Input string '{input_string}' does not match the required pattern [a-zA-Z]:[a-zA-Z]")
    left_string = match.group(1)
    right_string = match.group(2)
    return (left_string, right_string)

class EventEmitter(QObject):
    event_signal = pyqtSignal(IPCEvent)

class MainWindow(IPCQWidget):

    def __init__(self, ipc_manager: IPCManager):
        IPCQWidget.__init__(self, ipc_manager, ProcessType.GUI)
        self.logs.info("Starting MainWindow initialization")

        self.emitter = EventEmitter()
        self.emitter.event_signal.connect(self._dispatch_event)

        self.registry = PluginRegistry(ipc_manager)
        self.headspaces: Dict[str, Any] = {}

        def popup_callback():
            self.process_manager.send_event(
                    IPCEvent(
                        EventType.INTERACTION_COMPLETED,
                        ProcessType.GUI,
                        ProcessType.AI,
                        None
                    )
            )
        self.popup = AMIDialog(self, popup_callback)
        self.popup.setObjectName("convo_popup")

        try:
            screen = QApplication.primaryScreen()
            if not screen:
                raise RuntimeError("Primary Screen not found!")

            self.managed_layout = ManagedFlexiblePositioningLayout(screen.geometry())
            self.setLayout(self.managed_layout)
            self.setStyleSheet("background-color: black;")

            for plugin in self.registry.get_plugins_by_vertical(PluginVertical.GUI):
                self.managed_layout.add_plugin_widget(plugin.gui)

        except Exception as e:
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            self.logs.critical(f"Failed to initialize MainWindow: {tb_str}")

    def run(self):
        self.logs.debug("MainWindow.run() called! -> This is the show event")
        self.start_event_handler()
        self.managed_layout.setGeometry(self.managed_layout.screen_geometry)
        self.showFullScreen()

    def _handle_event(self, event: IPCEvent):
        """Handle a single event with proper error isolation."""
        if event.type in self.event_handlers:
            try:
                self.ipc_logs.debug(f"Handling {event.type}, inside thread")
                self.emitter.event_signal.emit(event)

            except Exception as e:
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                self.ipc_logs.error(f"Error handling event {event.type}: {e}\nFull traceback:\n{tb_str}")
        else:
            self.ipc_logs.warning(f"Unhandled event type: {event.type}")

    @pyqtSlot(IPCEvent)
    def _dispatch_event(self, event: IPCEvent):
        """Dispatch the event to the appropriate callback in the main thread."""
        if event.type in self.event_handlers:
            try:
                callback = self.event_handlers[event.type]
                self.ipc_logs.debug(f"Handling {event.type} with {callback.__name__}, in main thread")
                callback(event)
            except Exception as e:
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                self.ipc_logs.error(f"Error handling event {event.type}: {e}\nFull traceback:\n{tb_str}")

    @on_event(EventType.HOTWORD_DETECTED)
    def on_hotword_detection(self, event: IPCEvent):
        """Handle hotword detection by showing the popup"""
        self.popup.show_listening()

    @on_event(EventType.TRANSCRIPTION_READY)
    def on_transcription(self, event: IPCEvent):
        """Handle transcription by updating the popup"""
        self.popup.show_transcription(event.data)

    @on_event(EventType.RESPONSE_READY)
    def on_response(self, event: IPCEvent):
        """Handle AI response by updating the popup"""
        self.popup.show_response(event.data)

    @on_event(EventType.RELOAD_GUI)
    def reload_plugin_gui(self, event: IPCEvent):
        """Reload plugin widgets specified in the event data."""
        self.logs.info(f"Reload GUI triggered for {str(event.data)}")
        for plugin_name in event.data:
            self.managed_layout.update_plugin_widget(plugin_name)

    @on_event(EventType.INLINE_POPUP)
    def inline_popup(self, event: IPCEvent):
        """Reload plugin widgets specified in the event data."""
        self.logs.info(f"Reload GUI triggered for {str(event.data)}")
        try:
            headspace, method = parse_colon_string(event.data)
            headspace = self.managed_layout[headspace]
#           headspace = self.managed_layout.get_headspace(headspace)
            popup_inline_widget_getter = getattr(headspace, method)
            self.popup.append_widget_inline(popup_inline_widget_getter())
        except Exception as e:
            raise e
