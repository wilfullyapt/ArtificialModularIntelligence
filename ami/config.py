"""
This `config` module manages all interactions with the `config.yaml` file
"""

import os
from pathlib import Path
from typing import Any, Dict
import yaml

from ami.logger import Logger, LoggerConfig

def get_config_filepath() -> Path:
    """ The config filepath is hardcoded relitive to this file """
    return Path(__file__).parent.parent / "config.yaml"

class Config:
    """ Config class """
    _instance = None
    _config_filepath: Path|None = None
    _config: Dict = {}
    _count: int = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._config_filepath = get_config_filepath()

            with open(cls._config_filepath, 'r', encoding='utf-8') as file:
                try:
                    cls._config = yaml.safe_load(file)
                except yaml.YAMLError as exc:
                    print(exc)

        cls._count += 1
        return cls._instance

    def __getitem__(self, key):
        return self._config.get(key, None)

    def get(self, value, default=None) -> Any:
        """ Outward facing get method to use config like a dict for config.yaml """
        value = self[value]
        if value is None:
            return default
        return value

    @property
    def keys(self):
        """ All the elements of the config """
        return list(self._config.keys())

    @property
    def dict(self):
        """ All the elements of the config as a dict """
        return self._config

    @property
    def root(self):
        """ Relitive to this config.py file, the AMI root repo dir | DO NOT CHANGE """
        return Path(__file__).parent.parent

#---------------- LOGGING SPECIFIC

    @property
    def log_config(self):
        """ Get the logger config in accordance to the config """
        log_config: Dict[str, Any] = self.get("logging")
        return LoggerConfig(
                stdout=log_config.get("stdout", True),
                save_dir=self.ai_dir / log_config.get("directory", "logs"),
                log_level=log_config.get("level", "INFO")
        )

    def load_blank_logging(self):
        """ Get a logging object with config from config.yaml per self.log_config """
        return Logger(self.log_config)

#---------------- AI SPECIFIC

    @property
    def ai_dir(self):
        """ Get the Path of the AI file system """
        ai_dir_path = self.root / self["ai_filesystem"]
        ai_dir_path.mkdir(parents=True, exist_ok=True)
        return ai_dir_path

    @property
    def hot_word(self):
        """ Get the Path for the hot word file """
        return self.ai_dir / self["hot_word"]

    @property
    def recordings_dir(self):
        """ Get the Path for where to put the audio recording """
        if self.get("recording_dir") is None:
            return None
        recordings_dir = self.ai_dir / self["recording_dir"]
        recordings_dir.mkdir(parents=True, exist_ok=True)
        return recordings_dir

    @property
    def headspaces_dir(self):
        """ Get the Path for the headspaces sub filesystem """
        headspaces_dir = self.ai_dir / "headspaces"
        headspaces_dir.mkdir(parents=True, exist_ok=True)
        return headspaces_dir

    @property
    def server_port(self):
        """ Get the server port per the config """
        return self.get('port')

    @property
    def server_host(self):
        """ Get the host per the config """
        return self.get('host')

    @property
    def enabled_headspaces(self) -> list:
        """ Get the enabled headspaces per the config as a tuple """
        return tuple(self.get('enabled_headspaces', default=[]))

#---------------- GUI SPECIFIC

    @property
    def modules_dir(self):
        """ Get the path to the add on headspace modules per the config """
        if self.get("modules_dir") is None:
            return self.root / "modules"
        return self.root / self["modules_dir"]

    def enable_langsmith(self):
        """ Developer shortcut to enable LangSmith """
        os.environ['LANGCHAIN_API_KEY'] = self["langsmith_apikey"]
        os.environ['LANGCHAIN_TRACING_V2'] = "true"
