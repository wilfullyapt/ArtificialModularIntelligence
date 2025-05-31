""" Main full screen UI for the AMI system """

import traceback

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from ami.core import Config, PluginRegistry, PluginVertical
from ami.ipc import IPCManager, ProcessType, EventType, IPCQWidget, IPCEvent, on_event

from .popup import AMIDialog
from .layouts import FlexiblePositioningLayout

class MainWindow(IPCQWidget):

    def __init__(self, ipc_manager: IPCManager):
        IPCQWidget.__init__(self, ipc_manager, ProcessType.GUI)
        self.logs.info("Starting MainWindow initialization")

        self.registry = PluginRegistry(ipc_manager)

        # Create single popup instance
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

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |                     # Remove window frame
            Qt.WindowType.MaximizeUsingFullscreenGeometryHint       # Use full screen geometry
        )
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)   # Enable OpenGL acceleration if available

        try:
            # Setup the GUI
            self.layout_ = FlexiblePositioningLayout()
            self.setLayout(self.layout_)
            self.setStyleSheet("background-color: black;")

            # Iterate over the plugins with GUI and dynamically add them to the layout
            for plugin in self.registry.get_plugins_by_vertical(PluginVertical.GUI):
                widget = plugin.gui(self)
                self.layout_.add_widget(widget, **widget.placement)
                self.logs.info(f"Added {widget.name} with placement: {widget.placement}")

            # Setup screen management
            self.screen_timer = QTimer(self)
            self.screen_timer.timeout.connect(self.check_screen_changes)
            self.screen_timer.start(1000)  # Check screen changes every second

        except Exception as e:
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            self.logs.critical(f"Failed to initialize MainWindow: {tb_str}")

    def check_screen_changes(self):
        """Monitor and handle screen geometry changes"""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                geometry = screen.geometry()
                if geometry != self.geometry():
                    self.ensure_proper_screen_geometry()
        except Exception as e:
            self.logs.error(f"Error checking screen changes: {e}")

    def ensure_proper_screen_geometry(self):
        """Ensure window uses full screen geometry"""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                geometry = screen.geometry()
                self.setGeometry(geometry)
                self.layout_.setGeometry(geometry)
        except Exception as e:
            self.logs.error(f"Error setting screen geometry: {e}")

    def _show(self):
        # Show fullscreen
        self.showFullScreen()
        self.ensure_proper_screen_geometry()

    def showEvent(self, event):
        """Handle show event to ensure proper fullscreen"""
        super().showEvent(event)
        self.ensure_proper_screen_geometry()

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

