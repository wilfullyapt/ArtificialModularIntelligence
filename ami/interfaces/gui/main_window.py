""" Main full screen UI for the AMI system """

import time
from multiprocessing import Event, Queue

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget

from ami.base import Base
from ami.config import Config
from ami.core import Brain, AudioProcessor, ProcessState, VoiceEvent
from ami.core.headspace_importer import import_headspace
from ami.interfaces.gui.layouts import FlexiblePositioningLayout
from ami.interfaces.gui.popup import AMIDialog
from ami.interfaces.gui.widgets import builtin_widgets
from ami.interfaces.web.manager import FlaskManager

class MainWindow(QMainWindow, Base):

    def __init__(self):
        super().__init__()
        self.logs.info("Starting MainWindow initialization")
        self.brain = Brain()
        self.flask_manager = FlaskManager()
        self.popup = None

        self.listening_event_queue = Queue()
        self.listening_control_event = Event()
        self.listening_state_queue = Queue()
        self.audio_process = None

        config = Config()
        self.enabled_headspaces = config.enabled_headspaces
        self.enabled_headspaces = [ 'calendar' ]

        self.spawn_server()
        self.setup_ui(config.get('builtin_config', {}))

        self.server_check_timer = QTimer()
        self.server_check_timer.timeout.connect(self.check_server_messages)
        self.server_check_timer.start(100)  # Check every 100ms

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
            widget = WidgetClass(config.get(widget_name, {}))
#           widget.setStyleSheet(f"{widget.styleSheet()}; border: 1px solid red;")
            self.layout_.addWidget(widget, **widget.placement)
            self.logs.info(f"Added {widget_name} with placement: {widget.placement}")

        for widget_name in self.enabled_headspaces:
            module = import_headspace(widget_name, extract='widget')
            if hasattr(module, widget_name.capitalize()):
                WidgetClass = getattr(module, widget_name.capitalize())
                widget = WidgetClass()
                if widget.is_valid():
                    widget.render_widget()
                    self.layout_.addWidget(widget, **widget.placement)
                    self.logs.info(f"Added {widget_name} with placement: {widget.placement}")

        self.setWindowTitle('Artificial Modular Intelligence')


    def handle_voice_query(self, query: str):
        """ Connection point between voice input and Brain query processing """
#       if not self.popup or not self.popup.isVisible():
#           self.popup = Popup(self)
#           self.popup.show()
        self.popup.update_content(role="Human", text=query)
        time.sleep(4)
        self.popup.update_content(role="AI", text=query[::-1], expand=False)
        self.popup.start_timeout()

    def spawn_server(self):
        """Start the Flask server"""
        self.flask_manager.spawn_server_process(self.enabled_headspaces)
        self.logs.info(f"Flask server started at: {self.flask_manager.url}")

    def check_server_messages(self):
        """Check for messages from the server"""
        if hasattr(self, 'flask_manager'):
            message = self.flask_manager.receive_from_server()
            if message:
                self.handle_server_message(message)

    def handle_server_message(self, message):
        """Handle messages received from server"""
        message_type = message.get('type')
        data = message.get('data')

        if message_type == 'log':
            self.logs.info(f"Server log: {data}")
        elif message_type == 'error':
            self.logs.error(f"Server error: {data}")
        # Add other message types as needed

    def send_to_server(self, message_type, data):
        """Send message to server"""
        if hasattr(self, 'flask_manager'):
            self.flask_manager.send_to_server({
                'type': message_type,
                'data': data
            })

    def handle_voice_event(self, event_type, data):
        """ This is the signal reciever from the listening to handle events and data payloads """


        if event_type == VoiceEvent.HOTWORD_DETECTED:
            self.logs.info(f"VoiceEvent.HOTWORD_DETECTED")
            if self.popup is None:
                self.popup = AMIDialog(self)
            self.popup.start_listening()

        elif event_type == VoiceEvent.TRANSCRIPTION:
            self.logs.info(f"VoiceEvent.TRANSCRIPTION: {data}")
            if self.popup:
                self.popup.show_human_message(data)
                self.popup.prepare_ai_response()
                time.sleep(4)
                self.popup.show_ai_message(data[::-1], expand=False)
            self.listening_state_queue.put(ProcessState.HOTWORD_DETECTION)

        elif event_type == VoiceEvent.TIMEOUT:
            self.logs.info(f"VoiceEvent.TIMEOUT: {data}")

        elif event_type == VoiceEvent.ERROR:
            self.logs.info(f"VoiceEvent.ERROR: {data}")

        elif event_type == VoiceEvent.STATE_CHANGED:
            self.logs.info(f"VoiceEvent.STATE_CHANGED: {data}")

        else:
            self.logs.warn(f"VoiceEvent cannot be confirmed: {event_type}, {data}")

    def check_listening_events(self):
        """ Ran on the interval for self.check_timer """
        try:
            event_type, data = self.listening_event_queue.get_nowait()
            self.handle_voice_event(event_type, data)
        except:
            pass

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

        self.flask_manager.stop()

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

        print("main_window.cleanup(): debug flag is False. destroying children.")
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
