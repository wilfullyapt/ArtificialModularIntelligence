""" Main full screen UI for the AMI system """

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from ami.core import Config
from ami.gui.layouts import FlexiblePositioningLayout
from ami.ipc import IPCManager, ProcessType, EventType, IPCQWidget
from ami.ipc.base import on_event
from ami.ipc.manager import IPCEvent

from .popup import AMIDialog
from .widgets import builtin_widgets

class MainWindow(IPCQWidget):

    def __init__(self, ipc_manager: IPCManager):
        IPCQWidget.__init__(self, ipc_manager, ProcessType.GUI)
        self.logs.info("Starting MainWindow initialization")

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

        # Set window properties for fullscreen
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |                 # Remove window frame
            Qt.WindowType.MaximizeUsingFullscreenGeometryHint   # Use full screen geometry
        )

        # Enable OpenGL acceleration if available
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        try:
            config = Config()
            self.enabled_headspaces = config.enabled_headspaces
#           self.enabled_headspaces = [ 'calendar' ]

            # Setup UI and IPC
            self.setup_ui(config.get('builtin_config', {}))

            # Setup screen management
            self.screen_timer = QTimer(self)
            self.screen_timer.timeout.connect(self.check_screen_changes)
            self.screen_timer.start(1000)  # Check screen changes every second

        except Exception as e:
            self.logs.critical(f"Failed to initialize MainWindow: {e}")

    def setup_ui(self, config: dict):
        # Set up the main layout
        self.layout_ = FlexiblePositioningLayout()
        self.setLayout(self.layout_)

        # Set background and style
        self.setStyleSheet("background-color: black;")

        # Add builtin widgets
        for widget_name, WidgetClass in builtin_widgets.items():
            widget = WidgetClass(config.get(widget_name, {}))
            self.layout_.addWidget(widget, **widget.placement)
            self.logs.info(f"Added {widget_name} with placement: {widget.placement}")

        # Add headspace widgets
        for widget_name in self.enabled_headspaces:
            module = self.process_manager.registry[widget_name].gui()
            module = import_headspace(widget_name, extract='widget')
            if hasattr(module, widget_name.capitalize()):
                WidgetClass = getattr(module, widget_name.capitalize())
                widget = WidgetClass()
                if widget.is_valid():
                    widget.render_widget()
                    self.layout_.addWidget(widget, **widget.placement)
                    self.logs.info(f"Added {widget_name} with placement: {widget.placement}")

        # Show fullscreen
        self.showFullScreen()
        self.ensure_proper_screen_geometry()

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

