""" eary.py """
import os
import shutil
from pathlib import Path
from threading import Thread

import speech_recognition as sr
from snowboy import snowboydecoder

from ami.base import Base
from ami.config import Config

SENSITIVITY = 0.3
SILENCE_THRESHOLD = 5

class Ears(Base):
    """
        Ears the module that listens!

        r: sr.Recognizer = sr.Recognizer()
        detector: snowboydecoder.HotwordDetector = snowboydecoder.HotwordDetector(model_path)
            The snowboy Hotword Detector is an offline model that pick up on a specific word said
        talk_gap: int
            This is set in the config.yaml file as silence_threshold, defualted to SILENCE_THRESHOLD
            Talk Gap is fed into Ears.detector.start as a kwarg: silent_count_threshold

        References:

        snowboydecoder.HotwordDetector:
            https://github.com/seasalt-ai/snowboy/tree/master?tab=readme-ov-file#quick-start-for-python-demo


    """

    def __init__(self, temp_comms):
        """
        Initialize the Ears class.

        Args:
            temp_comms (TempComms): An instance of the TempComms class for communication.

        Attributes:
            temp_comms (TempComms): An instance of the TempComms class for communication.
            thread (Thread): A thread object for running the hotword detection.
            r (Recognizer): A speech recognition recognizer instance.
            model (str): The path to the hotword detection model.
            detector (HotwordDetector): A hotword detector instance.
            running (bool): A flag indicating whether the hotword detection is running.
            talk_gap (int): The silence threshold for detecting the end of speech.
            recordings_directory (Path): The directory path for storing audio recordings.
        """
        super().__init__()

        self.temp_comms = temp_comms
        self.thread = None

        self.r = sr.Recognizer()
        config = Config()

        self.model = str(config.hot_word)
        self.detector = snowboydecoder.HotwordDetector(self.model, sensitivity=SENSITIVITY)
        self.running = False

        self.talk_gap = int(config.get("silence_threshold", SILENCE_THRESHOLD))
        self.recordings_directory = config.recordings_dir

    def handle_audio_file(self, fname) -> None:
        """ Based on class parameters, delete or move the recording file """
        if self.recordings_directory is None:
            self.logs.warn(f"Ears.recordings_directory not found! Deleting {fname}.")
            os.remove(fname)
        else:
            if not self.recordings_directory.is_dir():
                self.recordings_directory.mkdir()
            shutil.move(Path(fname), self.recordings_directory / fname)

    def string_from_audio(self, fname) -> str:
        """ Convert the audio file to text """
        self.logs.info(f" Audio to text in progress ... {fname}")
        self.temp_comms.publish("gui.popup.loading_message", "Transcribing Audio")

        with sr.AudioFile(fname) as source:
            audio = self.r.record(source)

        try:
#           text = self.r.recognize_sphinx(audio)      # sphinx is local
            text = self.r.recognize_google(audio)      # google is the cloud

            self.handle_audio_file(fname)
            return text

        except sr.UnknownValueError:
            self.logs.error("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            self.logs.error(f"Could not request results for speech recognition service; {e}")
            return ""

    def _on_detection(self):
        """ Detection callback """
        self.temp_comms.publish("ears.hotword_detected")

    def _on_recorder_callback(self, fname):
        """ Recording finished callback """
        message = self.string_from_audio(fname)
        self.temp_comms.publish("ears.recorder_callback", message)

    def _hotword_listen(self):
        """ Inner start listening method """
#       passthru_keys are meant to be the arguement names for self.detector.start
#       passthru_keys = ["detected_callback", "interrupt_check", "sleep_time",
#                        "audio_recorder_callback", "silent_count_threshold", "recording_timeout"]
        try:
            while self.running:
                self.detector.start(detected_callback=self._on_detection,
                                    audio_recorder_callback=self._on_recorder_callback)
        except KeyboardInterrupt:
            self.running = False
            self.logs.info(" <ctlr-C> detected!!")
            if self.detector:
                self.detector.terminate()

    def listen(self):
        """ Start listening """
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._hotword_listen, daemon=True)
            self.logs.info("Ears running!")
            self.thread.start()

    def stop(self):
        """ Stop listening """
        if self.running:
            self.running = False
            if self.detector:
                self.logs.info("Detector Terminated!")
                self.detector.terminate()
            if self.thread:
                self.logs.info("Listener thread.join() called!")
                self.thread.join()
            self.logs.info("Ears stopped!")

#     TODO Implement Calibration
#     def calibrate_sensitivity(self, sensitivity_range=(.1, 4), interval=.2):
#         start_sensitivity = sensitivity_range[0]
#         end_sensitivity = sensitivity_range[-1]
