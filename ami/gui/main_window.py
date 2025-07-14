""" Main full screen UI for the AMI system """

import traceback

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from ..core import PluginRegistry, PluginVertical
from ..ipc import IPCManager, ProcessType, EventType, IPCQWidget, IPCEvent, on_event

from .popup import AMIDialog
from .layouts import ManagedFlexiblePositioningLayout

class MainWindow(IPCQWidget):

    def __init__(self, ipc_manager: IPCManager):
        IPCQWidget.__init__(self, ipc_manager, ProcessType.GUI)
        self.logs.info("Starting MainWindow initialization")

        self.registry = PluginRegistry(ipc_manager)

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

#       self.setWindowFlags(
#           Qt.WindowType.FramelessWindowHint |                     # Remove window frame
#           Qt.WindowType.MaximizeUsingFullscreenGeometryHint       # Use full screen geometry
#       )
#       self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)   # Enable OpenGL acceleration if available

        try:
            screen = QApplication.primaryScreen()
#           if not screen:
#               raise RuntimeError("Primary Screen not found!")

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
        self.managed_layout.setGeometry(self.managed_layout.screen_geometry)
        self.showFullScreen()

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
