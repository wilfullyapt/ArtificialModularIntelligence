""" eary.py """
import io
import time
import traceback
from pathlib import Path
from threading import Thread

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

class ListeningTimeout(Exception):
    """Exception raised when listening timeout occurs."""
    pass

class Ears(Base):
    """
    A class for handling audio input, hotword detection, and speech-to-text conversion.

    This class uses OpenWakeWord for hotword detection and Google Speech Recognition
    for speech-to-text conversion. It runs in a separate thread to continuously listen
    for a specified hotword and then record and transcribe subsequent audio input.

    Attributes:
        temp_comms (TempComms): An instance of the TempComms class for communication.
        thread (Thread): A thread object for running the hotword detection.
        r (Recognizer): A speech recognition recognizer instance.
        model (openwakeword.Model): An OpenWakeWord Model instance.
        running (bool): A flag indicating whether the hotword detection is running.
        LISTENING_PATIENCE (int): The gap between when the Human stops speaking and when the Ears ingest the command.
        SILENCE_THRESHOLD (int): The minimum threshold that determines if there is silence.

    Methods:
        get_model: Get or download the hotword detection model.
        string_from_audio: Convert audio data to text.
        listen: Continuously listen for the hotword and process audio input.
        start_listening: Start the listening thread.
        stop: Stop the listening thread.
    """
    def __init__(self, temp_comms):
        """
        Initialize the Ears class.

        Args:
            temp_comms: An instance of the TempComms class for communication.

        This method sets up the initial state of the Ears object, including:
        - Configuring audio processing parameters
        - Setting up the speech recognition recognizer
        - Loading the hotword detection model
        - Initializing various attributes for audio processing and recording
        """
        super().__init__()
        self.CHUNK = 1280
        self.DETECTION_THRESHOLD = 0.5

        self.temp_comms = temp_comms
        self.thread = None

        self.r = sr.Recognizer()
        config = Config()

        self.LISTENING_PATIENCE = config.listening_patience
        self.LISTENING_TIMEOUT = config.listening_timeout
        self.SILENCE_THRESHOLD = config.silence_threshold
        self.logs.info(f"SILENCE_THRESHOLD is {self.LISTENING_PATIENCE} seconds")
        self.logs.info(f"LISTENING_PATIENCE is {self.LISTENING_PATIENCE}")
        self.logs.info(f"SILENCE_THRESHOLD is {self.SILENCE_THRESHOLD}")

        self.model = self.get_model(
            config.oww_models_dir,
            config.hot_word,
            melspec_model_path=str(get_melspec_filepath(config.oww_models_dir)),
            embedding_model_path=str(get_embeddings_filepath(config.oww_models_dir))
        )

        self.running = False

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

    def string_from_audio(self, audio_data) -> str:
        """ Convert the audio data to text """
        self.logs.info("Audio to text in progress...")
        self.temp_comms.publish("gui.popup.loading_message", "Transcribing Audio")

        try:
            audio = sr.AudioData(audio_data.getvalue(), sample_rate=16000, sample_width=2)
            text = self.r.recognize_google(audio)      # google is the cloud
#           text = self.r.recognize_sphinx(audio)      # sphinx is local
            self.logs.info("recognize_google used for audio STT")
            return text

        except sr.UnknownValueError:
            self.logs.error("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            self.logs.error(f"Could not request results for speech recognition service; {e}")
            return ""

    def listen(self):
        """
        Continuously listen for the hotword and process audio input.

        This method opens a microphone stream and continuously analyzes the audio input
        for the presence of a hotword. When the hotword is detected, it starts recording
        the subsequent audio until a period of silence is detected. The recorded audio
        is then transcribed to text and published via temp_comms.

        The method runs in a loop while self.running is True, allowing it to be stopped
        externally by setting self.running to False.

        Note:
            This method is intended to be run in a separate thread to avoid blocking
            the main program execution.
        """
        p = pyaudio.PyAudio()
        mic_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        audio_buffer = []
        silence_counter = 0
        last_minute_buffer = []

        self.logs.debug("Listening started ...")

        try:
            while self.running:
                audio = np.frombuffer(mic_stream.read(self.CHUNK), dtype=np.int16)
                last_minute_buffer.append(audio)
                if len(last_minute_buffer) > 60 * 16000 // self.CHUNK:  # Keep last minute of audio
                    last_minute_buffer.pop(0)

                prediction = self.model.predict(audio)
                detection = any(self.model.prediction_buffer[mdl][-1] > self.DETECTION_THRESHOLD
                    for mdl in self.model.prediction_buffer.keys()
                )

                if detection:
                    self.temp_comms.publish("ears.hotword_detected")
                    self.logs.debug("Hotword detected!")
                    last_minute_audio = np.concatenate(last_minute_buffer)
                    positive_audio = np.abs(last_minute_audio)
                    min_amplitude = np.min(positive_audio)
                    max_amplitude = np.max(positive_audio)
                    std_amplitude = np.std(positive_audio)
                    calc_threshold = (min_amplitude*2)+std_amplitude
                    silence_threshold = max(calc_threshold, self.SILENCE_THRESHOLD)
#                   silence_threshold = max((min_amplitude*2)+std_amplitude, 10_000)
                    self.logs.debug(f"Listening... min={min_amplitude}, calc={calc_threshold}, std={std_amplitude}, threshold={silence_threshold}")

                    audio_buffer = [audio]
                    silence_counter = 0
                    speech_started = False
                    start_time = time.time()

                    while silence_counter < self.LISTENING_PATIENCE and self.running:
                        audio = np.frombuffer(mic_stream.read(self.CHUNK), dtype=np.int16)
                        audio_buffer.append(audio)

                        if time.time() - start_time > 1 and not speech_started:
                            if np.max(np.abs(audio)) > silence_threshold:
                                speech_started = True
                                start_time = time.time()
                            else:
                                if self.logs.level in [ 'DEBUG', 'INFO' ]:
                                    print(f"\rTimeout Counter: {time.time() - start_time:.1f}/{self.LISTENING_TIMEOUT} | threshold={np.max(np.abs(audio))}", end="", flush=True)

                        if speech_started:
                            if self.logs.level in [ 'DEBUG', 'INFO' ]:
                                print(f"\rSilence threshold: {np.max(np.abs(audio))} | {np.max(np.abs(audio))/silence_threshold}", end="", flush=True)
                            if np.max(np.abs(audio)) < silence_threshold:
                                silence_counter = time.time() - start_time
                            else:
                                start_time = time.time()
                                silence_counter = 0

                        if time.time() - start_time > self.LISTENING_TIMEOUT:
                            raise ListeningTimeout("Listening timeout occurred")

                    audio_data = np.concatenate(audio_buffer)
                    with io.BytesIO() as f:
                        sf.write(f, audio_data, 16000, format='wav')
                        text = self.string_from_audio(f)

                    self.temp_comms.publish("ears.recorder_callback", text)
                    self.logs.info(f"Transcribed text: {text}. Listening finished.")
                    break

        except ListeningTimeout:
            self.logs.warn("Listening Timeout occurred. Ending interaction.")
            self.temp_comms.publish("ears.timeout")

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            self.logs.error(f"An error occurred: {type(e).__name__} - {str(e)}")

            for frame in tb:
                filename, lineno, func, text = frame
                log_message = f"File {filename}, line {lineno}, in {func}"
                if text:
                    log_message += f"\n    {text}"
                self.logs.error(log_message)

        finally:
            self.running = False
            mic_stream.stop_stream()
            mic_stream.close()
            p.terminate()
            self.model.reset()
            self.logs.info("Thread Exiting")

    def start_listening(self):
        """ Start Listening """
        time.sleep(0.5)
        if not self.running:
            self.running = True
            self.thread = Thread(target=self.listen, daemon=True)
            self.logs.info("Ears running!")
            self.thread.start()

    def stop(self):
        """ Stop listening """
        if self.running:
            self.running = False
            if self.thread:
                self.logs.info("Listener thread.join() called!")
                self.thread.join()
            self.logs.info("Ears stopped!")

#     TODO Implement Calibration
#     def calibrate_sensitivity(self, sensitivity_range=(.1, 4), interval=.2):
#         start_sensitivity = sensitivity_range[0]
#         end_sensitivity = sensitivity_range[-1]
