""" Hotword detection and listening functionality using OpenWakeWord and Silero VAD models """

from enum import Enum, auto
import io
import time
import traceback
from pathlib import Path
from typing import Any, Callable
from threading import Thread

import pyaudio
import numpy as np
import speech_recognition as sr
import openwakeword
from openwakeword.utils import download_models
from openwakeword.model import Model
import soundfile as sf
import requests
from silero_vad.utils import init_jit_model, VADIterator

from ami.core import Config, LogBase
from ami.ipc import EventType

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

class ListenerState(Enum):
    """Enum representing the different states of the Listener."""
    IDLE = auto()
    WAITING_HOTWORD = auto()
    LISTENING = auto()

class InvalidModel(Exception):
    """Exception raised for invalid hotword models."""
    pass

class ListeningTimeout(Exception):
    """Exception raised when listening timeout occurs."""
    pass

class Listener(LogBase):
    """
    A class for handling audio input, hotword detection, and speech-to-text conversion.

    This class uses OpenWakeWord for hotword detection and Silero VAD for speech detection,
    followed by Google Speech Recognition for speech-to-text conversion. It runs in a separate
    thread to continuously listen for a specified hotword and then record and transcribe
    subsequent audio input.

    Attributes:
        event_handler (Callable): Callback function to handle events.
        thread (Thread): Thread object for running the detection.
        r (Recognizer): Speech recognition recognizer instance.
        model (openwakeword.Model): OpenWakeWord Model instance for hotword detection.
        vad_model: Silero VAD model for voice activity detection.
        running (bool): Flag indicating whether detection is running.
        LISTENING_PATIENCE (int): Duration to wait after speech ends (overridden by VAD).
        LISTENING_TIMEOUT (int): Maximum listening duration.
        SILENCE_THRESHOLD (int): Legacy threshold, used as fallback.
    """
    def __init__(self, event_handler: Callable[[EventType, Any], None]):
        """
        Initialize the Listener class with hotword and VAD models.

        Args:
            event_handler: Callback function to handle events. Takes EventType and str parameters.


        This method sets up the initial state of the Listener object, including:
            - Configuring audio processing parameters
            - Setting up the speech recognition recognizer
            - Loading the hotword detection model
            - Loading the voice audio detection model
            - Initializing various attributes for audio processing and recording
        """
        super().__init__()
        self.event_handler = event_handler
        self.CHUNK = 1280

        self.thread = None
        self.r = sr.Recognizer()
        self.state = ListenerState.IDLE
        config = Config()

        self.DETECTION_THRESHOLD = config.detection_threshold
        self.LISTENING_PATIENCE = config.listening_patience
        self.LISTENING_TIMEOUT = config.listening_timeout
        self.SILENCE_THRESHOLD = config.silence_threshold
        self.logs.debug(f"DETECTION_THRESHOLD is {self.DETECTION_THRESHOLD}")
        self.logs.debug(f"LISTENING_PATIENCE is {self.LISTENING_PATIENCE}")
        self.logs.debug(f"LISTENING_TIMEOUT is {self.LISTENING_TIMEOUT}")
        self.logs.debug(f"SILENCE_THRESHOLD is {self.SILENCE_THRESHOLD}")

        self.model = self.get_model(
            config.oww_models_dir,
            config.hot_word,
            melspec_model_path=str(get_melspec_filepath(config.oww_models_dir)),
            embedding_model_path=str(get_embeddings_filepath(config.oww_models_dir))
        )

        vad_model_path = self.download_silero_vad_model(config.oww_models_dir)
        self.vad_model = init_jit_model(str(vad_model_path))

        self.running = False

    def download_silero_vad_model(self, models_dir: Path) -> Path:
        """
        Download the Silero VAD model to the specified directory if not present.

        Args:
            models_dir (Path): Directory to store the model.

        Returns:
            Path: Path to the downloaded or existing model file.
        """
        model_filename = "silero_vad.jit"
        model_path = models_dir / model_filename
        if not model_path.exists():
            url = "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.jit"
            response = requests.get(url)
            response.raise_for_status()
            with open(model_path, "wb") as f:
                f.write(response.content)
            self.logs.info(f"Downloaded {model_filename} to {models_dir}")
        else:
            self.logs.debug(f"{model_filename} already exists in {models_dir}")
        return model_path

    def get_model(self, models_dir: Path, hotword: str, **kwargs) -> Model:
        """
        Get or download the hotword detection model.
        This method checks if a model for the specified hotword exists in the models directory.
        If found, it returns a Model instance using the existing file. If not found, it attempts
        to download the model from the OpenWakeWord repository. If the hotword is not valid,
        it raises an InvalidModel exception.

        Args:
            models_dir (Path): The directory where models are stored.
            hotword (str): The name of the hotword to detect.

        Returns:
            Model: An instance of the OpenWakeWord Model class.

        Raises:
            InvalidModel: If the specified hotword is not valid.
        """
        tflite_files = list(models_dir.glob(f"*{hotword}*.tflite"))

        if len(tflite_files) > 0:
            return Model(wakeword_models=[str(tflite_files[0])], **kwargs)
        else:
            if hotword not in openwakeword.MODELS.keys():
                err_msg = f"Hotword {hotword} not valid. Please reconfigure with one of {openwakeword.MODELS.keys()}"
                self.logs.error(err_msg)
                raise InvalidModel(err_msg)
            else:
                download_models(model_names=[hotword], target_directory=str(models_dir))
                return self.get_model(models_dir, hotword, **kwargs)

    def string_from_audio(self, audio_data) -> str:
        """ Convert the audio data to text """
        self.logs.debug("Audio to text in progress...")

        try:
            audio = sr.AudioData(audio_data.getvalue(), sample_rate=16000, sample_width=2)
            text = self.r.recognize_google(audio)      # google is the cloud
#           text = self.r.recognize_sphinx(audio)      # sphinx is local
            self.logs.debug("recognize_google used for audio STT")
            return text
        except sr.UnknownValueError:
            self.logs.error("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            self.logs.error(f"Could not request results for speech recognition service; {e}")
            return ""

    def _handle_error(self, e):
        """Handle exceptions and log them appropriately."""
        tb = traceback.extract_tb(e.__traceback__)
        error_msg = f"An error occurred: {type(e).__name__} - {str(e)}"
        self.logs.error(error_msg)

        for frame in tb:
            filename, lineno, func, text = frame
            log_message = f"File {filename}, line {lineno}, in {func}"
            if text:
                log_message += f"\n    {text}"
            self.logs.error(log_message)

        self.event_handler(EventType.ERROR, error_msg)

    def capture_speech(self, mic_stream, initial_audio, silence_threshold):
        """
        Capture and process speech after hotword detection using Silero VAD.

        Args:
            mic_stream: The active microphone stream.
            initial_audio: The audio chunk where hotword was detected (not used directly in VAD).
            silence_threshold: Legacy threshold (used as fallback).
        """
        self.state = ListenerState.LISTENING
        vad_iterator = VADIterator(self.vad_model, return_probs=True)
        threshold = 0.5  # VAD speech detection threshold
        silence_duration = 2.0  # Stop after 2 seconds of silence
        chunk_duration = self.CHUNK / 16000.0  # Duration of each chunk in seconds
        start_time = time.time()
        audio_buffer = []

        try:
            # Wait for speech to start
            while self.running:
                audio = np.frombuffer(mic_stream.read(self.CHUNK), dtype=np.int16)
                audio_float = audio.astype(np.float32) / 32768.0  # Convert to float32 for VAD
                prob = vad_iterator(audio_float)
                if prob > threshold:
                    audio_buffer.append(audio)
                    break
                if time.time() - start_time > self.LISTENING_TIMEOUT:
                    raise ListeningTimeout("Listening timeout occurred")

            # Collect audio until 2 seconds of silence
            silence_time = 0.0
            while self.running:
                audio = np.frombuffer(mic_stream.read(self.CHUNK), dtype=np.int16)
                audio_float = audio.astype(np.float32) / 32768.0
                prob = vad_iterator(audio_float)
                audio_buffer.append(audio)
                if prob > threshold:
                    silence_time = 0.0
                else:
                    silence_time += chunk_duration
                if silence_time >= silence_duration:
                    break
                if time.time() - start_time > self.LISTENING_TIMEOUT:
                    raise ListeningTimeout("Listening timeout occurred")

            # Process the collected audio
            audio_data = np.concatenate(audio_buffer)
            with io.BytesIO() as f:
                sf.write(f, audio_data, 16000, format='wav')
                text = self.string_from_audio(f)

            if text:
                self.event_handler(EventType.TRANSCRIPTION_READY, text)
                self.logs.info(f"Listening finished; transcribed text: {text}")
            else:
                self.event_handler(EventType.ERROR, "Failed to transcribe audio")

        except ListeningTimeout:
            error_msg = "Listening Timeout occurred. Ending interaction."
            self.logs.warning(error_msg)
            self.event_handler(EventType.ERROR, error_msg)

        except Exception as e:
            self._handle_error(e)

        finally:
            self.state = ListenerState.IDLE
            self.running = False

    def wait_for_hotword(self):
        """
        Continuously listen for the hotword.
        This method opens a microphone stream and continuously analyzes the audio input
        for the presence of a hotword. When detected, it transitions to the listening state.
        """
        self.state = ListenerState.WAITING_HOTWORD
        p = pyaudio.PyAudio()
        mic_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        last_minute_buffer = []
        self.logs.debug("Waiting for hotword...")

        try:
            while self.running and self.state == ListenerState.WAITING_HOTWORD:
                audio = np.frombuffer(mic_stream.read(self.CHUNK), dtype=np.int16)
                last_minute_buffer.append(audio)
                if len(last_minute_buffer) > 60 * 16000 // self.CHUNK:          # Keep last minute of audio
                    last_minute_buffer.pop(0)

                prediction = self.model.predict(audio)
                detection = any(self.model.prediction_buffer[mdl][-1] > self.DETECTION_THRESHOLD
                    for mdl in self.model.prediction_buffer.keys()
                )

                if detection:
                    self.event_handler(EventType.HOTWORD_DETECTED, "")
                    self.logs.debug("Hotword detected!")
                    last_minute_audio = np.concatenate(last_minute_buffer)
                    positive_audio = np.abs(last_minute_audio)
                    min_amplitude = np.min(positive_audio)
                    std_amplitude = np.std(positive_audio)
                    calc_threshold = (min_amplitude*2)+std_amplitude
                    silence_threshold = max(calc_threshold, self.SILENCE_THRESHOLD)
                    self.logs.debug(f"Listening... min={min_amplitude}, calc={calc_threshold}, std={std_amplitude}, threshold={silence_threshold}")

                    # Start listening for speech
                    self.capture_speech(mic_stream, audio, silence_threshold)
                    break

        except Exception as e:
            self._handle_error(e)
            self.running = False

        finally:
            mic_stream.stop_stream()
            mic_stream.close()
            p.terminate()
            self.model.reset()
            self.logs.debug("Hotword detection ended")

    def start_listening(self):
        """Start the hotword detection thread."""
        time.sleep(0.5)
        if not self.running and self.state == ListenerState.IDLE:
            self.running = True
            self.thread = Thread(target=self.wait_for_hotword, daemon=True)
            self.thread.start()
        else:
            self.logs.warning(f"Cannot start listening! running='{str(self.running)}', state='{self.state}'")


    def capture_audio(self):
        """Start the hotword detection thread."""
        time.sleep(0.5)
        if not self.running and self.state == ListenerState.IDLE:
            self.running = True
            self.thread = Thread(target=self.capture_speech, daemon=True)
            self.logs.info(" -- Capturing audio prompt --")
            self.thread.start()

    def stop_listening(self):
        """Stop all listening operations."""
        if self.running:
            self.running = False
            if self.thread:
                self.logs.info("Listener thread.join() called!")
                self.thread.join()
            self.state = ListenerState.IDLE
            self.logs.info("Listening stopped!")
