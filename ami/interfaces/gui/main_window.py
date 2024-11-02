from PyQt6.QtWidgets import QMainWindow, QApplication
from ami.core.brain import Brain
from ami.core.listening import Ears



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_components()
        self.setup_ui()
        self.setup_voice_thread()
    
    def setup_components(self):
        # Initialize core components
        self.brain = Brain()
        self.ears = Ears()
        
        # Load headspaces
        self.load_headspaces()
    
    def setup_voice_thread(self):
        # Create voice detection thread
        self.voice_thread = VoiceThread(self.ears)
        self.voice_thread.query_detected.connect(self.handle_voice_query)
        
    def setup_ui(self):
        # Set up your UI components here
        pass
    
    def handle_voice_query(self, query: str):
        # Process query with brain
        response = self.brain.process_query(query)
        # Update UI with response
        self.update_response_display(response)
    
    def start(self):
        # Start voice detection
        self.voice_thread.start()
        
    def closeEvent(self, event):
        # Clean shutdown
        self.voice_thread.stop()
        self.voice_thread.wait()
        event.accept()

# ami/main.py

