""" Listening module | Hotword detection and query recording """

import io
import time
import signal
from enum import Enum
from pathlib import Path
import multiprocessing as mp

import numpy as np
import speech_recognition as sr
import pyaudio
import openwakeword
from openwakeword.utils import download_models
from openwakeword.model import Model
import soundfile as sf

from ami.base import Base
from ami.config import Config


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

class ProcessState(Enum):
    HOTWORD_DETECTION = "HOTWORD_DETECTION"
    LISTENING = "LISTENING"
    PAUSED = "PAUSED"

class VoiceEvent(Enum):
    HOTWORD_DETECTED = 'HOTWORD_DETECTED'
    TRANSCRIPTION = 'TRANSCRIPTION'
    TIMEOUT = 'TIMEOUT'
    ERROR = 'ERROR'
    STATE_CHANGED = 'STATE_CHANGED'

class AudioProcessor(mp.Process, Base):

    def __init__(self, event_queue: mp.Queue, state_queue: mp.Queue, control_event: mp.Event):
        super().__init__()
        Base.__init__(self)
        self.event_queue = event_queue
        self.state_queue = state_queue
        self.control_event = control_event

        config = Config()
        self.models_dir = config.oww_models_dir
        self.hot_word = config.hot_word

        self.CHUNK = 1280
        self.DETECTION_THRESHOLD = config.detection_threshold
        self.LISTENING_PATIENCE = config.listening_patience
        self.LISTENING_TIMEOUT = config.listening_timeout
        self.SILENCE_THRESHOLD = config.silence_threshold
        self.logs.info(f"DETECTION_THRESHOLD is {self.DETECTION_THRESHOLD}")
        self.logs.info(f"LISTENING_PATIENCE is {self.LISTENING_PATIENCE}")
        self.logs.info(f"SILENCE_THRESHOLD is {self.LISTENING_PATIENCE} seconds")
        self.logs.info(f"SILENCE_THRESHOLD is {self.SILENCE_THRESHOLD}")

    def get_model(self, models_dir: Path, hotword: str, **kwargs) -> Model:
        """
        Get or download the hotword detection model.

        Args:
            models_dir (Path): The directory where models are stored.
            hotword (str): The name of the hotword to detect.

        Returns:
            Model: An instance of the OpenWakeWord Model class.

        Raises:
            InvalidModel: If the specified hotword is not valid.

        This method checks if a model for the specified hotword exists in the models directory.
        If found, it returns a Model instance using the existing file. If not found, it attempts
        to download the model from the OpenWakeWord repository. If the hotword is not valid,
        it raises an InvalidModel exception.
        """
        tflite_files = list(models_dir.glob(f"*{hotword}*.tflite"))

        if len(tflite_files) > 0:
            return Model(wakeword_models=[str(tflite_files[0])], **kwargs)

        else:
            if hotword not in openwakeword.MODELS.keys():
                err_msg = f"Hotword {hotword} not valid. Please reconfigire with one of the following {openwakeword.MODELS.keys()}"
                self.logs.error(err_msg)
                raise InvalidModel(err_msg)
            else:
                download_models(model_names=[hotword], target_directory=str(models_dir))
                return self.get_model(models_dir, hotword, **kwargs)

    def record_speech(self, stream):
        audio_buffer = []
        silence_counter = 0
        start_time = time.time()
        speech_started = False
        self.logs.info("Speech Recording started")

        while silence_counter < self.LISTENING_PATIENCE and not self.control_event.is_set():
            audio = np.frombuffer(stream.read(self.CHUNK), dtype=np.int16)
            audio_buffer.append(audio)

            if time.time() - start_time > self.LISTENING_TIMEOUT:
                self.event_queue.put((VoiceEvent.TIMEOUT, None))
                return None

            # Your existing silence detection logic
            if np.max(np.abs(audio)) > self.SILENCE_THRESHOLD:
                speech_started = True
                start_time = time.time()
            elif speech_started:
                silence_counter = time.time() - start_time

        self.logs.info("Speech Recording finished")
        return np.concatenate(audio_buffer) if audio_buffer else None

    def string_from_audio(self, audio_data) -> str:
        try:
            recognizer = sr.Recognizer()
            audio = sr.AudioData(audio_data.getvalue(), sample_rate=16000, sample_width=2)
            text = recognizer.recognize_google(audio)      # google is the cloud
#           text = recognizer.recognize_sphinx(audio)      # sphinx is local
            return text
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    def run(self):
        """
        Continuously listen for the hotword and process audio input.

        This method opens a microphone stream and continuously analyzes the audio input
        for the presence of a hotword. When the hotword is detected, it starts recording
        the subsequent audio until a period of silence is detected. The recorded audio
        is then transcribed to text and published via temp_comms.

        The method runs in a loop while self.running is True, allowing it to be stopped
        externally by setting self.running to False.
        """

        signal.signal(signal.SIGINT, signal.SIG_IGN)        # Ignore SIGINT in child process to let parent handle it
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            self.model = self.get_model(
                self.models_dir,
                self.hot_word,
                melspec_model_path=str(get_melspec_filepath(self.models_dir)),
                embedding_model_path=str(get_embeddings_filepath(self.models_dir))
            )

            try:

                last_minute_buffer = []

                while not self.control_event.is_set():
                    # Read audio chunk
                    audio = np.frombuffer(stream.read(self.CHUNK), dtype=np.int16)
                    last_minute_buffer.append(audio)

                    # Maintain buffer size
                    if len(last_minute_buffer) > 60 * 16000 // self.CHUNK:
                        last_minute_buffer.pop(0)

                    # Hot word detection
                    prediction = self.model.predict(audio)
                    detection = any(
                        self.model.prediction_buffer[mdl][-1] > self.DETECTION_THRESHOLD
                        for mdl in self.model.prediction_buffer.keys()
                    )

                    print("\rDetection readings:", end="")
                    for mdl in self.model.prediction_buffer.keys():
                        print(f" {mdl}: {self.model.prediction_buffer[mdl][-1]:.4f}", end="")
                    print(f" | Threshold: {self.DETECTION_THRESHOLD:.4f}", end="\r", flush=True)

                    if detection:
                        # Signal hotword detection
                        self.event_queue.put((VoiceEvent.HOTWORD_DETECTED, None))
                        self.logs.info("Hotword detected.")

                        # Record and process speech
                        audio_data = self.record_speech(stream)

                        if audio_data is not None:
                            with io.BytesIO() as f:
                                sf.write(f, audio_data, 16000, format='wav')
                                text = self.string_from_audio(f)
                                if text:
                                    self.event_queue.put((VoiceEvent.TRANSCRIPTION, text))

                        break

            except Exception as e:
                self.logs.error(f"Error while listening ... {str(e)}")
                self.event_queue.put((VoiceEvent.ERROR, str(e)))
            finally:
                # Clean up audio resources
                stream.stop_stream()
                stream.close()
                p.terminate()
                self.model.reset()
                self.logs.info("Listening Finished")

        except Exception as e:
            self.logs.error(f"Failed to initialize audio: {str(e)}")
            self.event_queue.put((VoiceEvent.ERROR, f"Failed to initialize audio: {str(e)}"))
        finally:
            try:
                self.event_queue.close()
            except Exception as e:
                self.logs.warn(f"Error is closing the event queue: {e}")

