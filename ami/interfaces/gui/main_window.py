""" Main full screen UI for the AMI system """

import multiprocessing as mp

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

from ami.base import Base

from ami.core import Brain, AudioProcessor, ProcessState, VoiceEvent
from ami.interfaces.gui import builtin_widgets


class MainWindow(QMainWindow, Base):

    def __init__(self):
        super().__init__()
        self.brain = Brain()

        # Set up multiprocessing communication
        self.listening_event_queue = mp.Queue()
        self.listening_control_event = mp.Event()
        self.listening_state_queue = mp.Queue()
        self.audio_process = None

        # Initialize UI
        self.setup_ui()
        self.showFullScreen()

        # Set up event checking timer
        self.check_listen_timer = QTimer()
        self.check_listen_timer.timeout.connect(self.check_listening_events)
        self.check_listen_timer.start(100)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        """ Add the loop here from the Claude conversation """
        # Create and add the TimeDateWidget
        time_date_widget = TimeDateWidget()
        layout.addWidget(time_date_widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.setWindowTitle('AMI')  # Set window title

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

        if self.audio_process is not None:
            self.listening_control_event.set()              # Signal the process to stop

            self.audio_process.join(timeout=1.0)            # Give the process a chance to clean up

            if self.audio_process.is_alive():               # If still alive, terminate forcefully
                self.audio_process.terminate()
                self.audio_process.join(timeout=1.0)

                if self.audio_process.is_alive():           # Last resort: kill
                    self.audio_process.kill()

            while not self.listening_event_queue.empty():   # Clean up the queue
                try:
                    self.listening_event_queue.get_nowait()
                except:
                    break

            self.listening_event_queue.close()              # Close and unlink the queue
            self.listening_event_queue.join_thread()

            self.audio_process = None                       # Clear references

    def closeEvent(self, event):
        """Handle window close event"""
        self.cleanup()
        event.accept()
