from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


SENSITIVITY = 0.3

def get_melspec_filepath(models_dir: Path, search_string: str="melspectrogram", extension: str="tflite"):
    """ Get the melspec model for OpenWakeWord """
    for file in models_dir.glob(f"*{search_string}*.{extension}"):
        return file
    return None

def get_embeddings_filepath(models_dir: Path, search_string: str="embedding", extension: str="tflite"):
    """ Get the embeddings model for OpenWakeWord """
    for file in models_dir.glob(f"*{search_string}*.{extension}"):
        return file
    return None

class InvalidModel(Exception):
    """Exception raised for invalid hotword models."""
    pass

class ListeningTimeout(Exception):
    """Exception raised when listening timeout occurs."""
    pass

class VoiceThread(QThread):

    query_detected = pyqtSignal(str)

    def __init__(self, ears: Ears):
        super().__init__()
        self.ears = ears
        self.running = True

    def run(self):
        while self.running:
            if self.ears.detect_hotword():
                query = self.ears.capture_query()
                self.query_detected.emit(query)

    def stop(self):
        self.running = False
