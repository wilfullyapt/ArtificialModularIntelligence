""" Main full screen UI for the AMI system """

import multiprocessing as mp

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget

from ami.base import Base

from ami.config import Config
from ami.core import Brain, AudioProcessor, ProcessState, VoiceEvent
from ami.core.headspace_importer import import_headspace
from ami.interfaces.gui.layouts import FlexiblePositioningLayout
from ami.interfaces.gui.widgets import builtin_widgets

class MainWindow(QMainWindow, Base):

    def __init__(self):
        super().__init__()
        self.logs.info("Starting MainWindow initialization")
        self.brain = Brain()

        self.listening_event_queue = mp.Queue()
        self.listening_control_event = mp.Event()
        self.listening_state_queue = mp.Queue()
        self.audio_process = None

        config = Config()
        self.enabled_headspaces = config.enabled_headspaces
        self.setup_ui(config.get('builtin_config', {}))

        self.check_listen_timer = QTimer()
        self.check_listen_timer.timeout.connect(self.check_listening_events)
        self.check_listen_timer.start(100)

    def setup_ui(self, config: dict):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout_ = FlexiblePositioningLayout()
        central_widget.setLayout(self.layout_)

        central_widget.setStyleSheet("background-color: black;")
        self.showFullScreen()

        for widget_name, WidgetClass in builtin_widgets.items():
            self.logs.info(f"Creating widget: {widget_name}")
            widget = WidgetClass(config.get(widget_name, {}))
#           widget.setStyleSheet(f"{widget.styleSheet()}; border: 1px solid red;")
            self.layout_.addWidget(widget, **widget.placement)
            self.logs.info(f"Added {widget_name} with placement: {widget.placement}")

        for widget_name in self.enabled_headspaces:
            module = import_headspace(widget_name)
            if hasattr(module, 'widget'):
                if hasattr(module.widget, widget_name.capitalize()):
                    WidgetClass = getattr(module.widget, widget_name.capitalize())
                    widget = WidgetClass()
                    if widget.is_valid():
                        widget.render_widget()
                        self.layout_.addWidget(widget, **widget.placement)
                        self.logs.info(f"Added {widget_name} with placement: {widget.placement}")

        self.setWindowTitle('Artificial Modular Intelligence')

    def handle_voice_query(self, query: str):
        """ Connection point between voice input and Brain query processing """
        print(query, flush=True)
#       response = self.brain.process_query(query)
        # Update UI with response
#       self.update_response_display(response)

    def check_listening_events(self):
        """ Ran on the interval for self.check_timer """
        try:
            event_type, data = self.listening_event_queue.get_nowait()
            self.handle_voice_event(event_type, data)
        except:
            pass

    def handle_voice_event(self, event_type, data):
        """ This is the signal reciever from the listening to handle events and data payloads """

        if event_type == VoiceEvent.TRANSCRIPTION:
            self.logs.info(f"VoiceEvent.TRANSCRIPTION: {data}")
            self.handle_voice_query(data)
            self.listening_state_queue.put(ProcessState.HOTWORD_DETECTION)

        elif event_type == VoiceEvent.HOTWORD_DETECTED:
            self.logs.info(f"VoiceEvent.HOTWORD_DETECTED")

        elif event_type == VoiceEvent.TIMEOUT:
            self.logs.info(f"VoiceEvent.TIMEOUT: {data}")

        elif event_type == VoiceEvent.ERROR:
            self.logs.info(f"VoiceEvent.ERROR: {data}")

        elif event_type == VoiceEvent.STATE_CHANGED:
            self.logs.info(f"VoiceEvent.STATE_CHANGED: {data}")

        else:
            self.logs.warn(f"VoiceEvent cannot be confirmed: {event_type}, {data}")

    def start(self):
        """ Start up the audio process and the web server """
        if self.audio_process is None:
            self.audio_process = AudioProcessor(
                self.listening_event_queue,
                self.listening_state_queue,
                self.listening_control_event
            )
            self.audio_process.start()

    def cleanup(self):
        """Clean up resources and ensure process termination"""
        self.check_listen_timer.stop()

        # Clean up audio process
        if self.audio_process is not None:
            self.listening_control_event.set()
            self.audio_process.join(timeout=1.0)
            if self.audio_process.is_alive():
                self.audio_process.terminate()
                self.audio_process.join(timeout=1.0)
                if self.audio_process.is_alive():
                    self.audio_process.kill()

            while not self.listening_event_queue.empty():
                try:
                    self.listening_event_queue.get_nowait()
                except:
                    break

            self.listening_event_queue.close()
            self.listening_event_queue.join_thread()
            self.audio_process = None

        # Clean up widgets
        if hasattr(self, 'layout'):
            while self.layout_.count():
                item = self.layout_.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

    def closeEvent(self, event):
        """Handle window close event"""
        self.cleanup()
        event.accept()
