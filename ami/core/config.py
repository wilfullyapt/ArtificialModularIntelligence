"""
Enhanced config module that manages interactions with config.yaml file with real-time updates
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def get_config_filepath() -> Path:
    """The config filepath is hardcoded relative to this file"""
    return Path(__file__).parent.parent.parent / "config.yaml"

class ConfigFileHandler(FileSystemEventHandler):
    """Handles file system events for the config file"""
    def __init__(self, config_instance):
        self.config_instance = config_instance
        self.last_modified = 0
        self.debounce_interval = 0.5  # seconds

    def on_modified(self, event):
        if not event.is_directory:
            current_time = time.time()
            if current_time - self.last_modified > self.debounce_interval:
                self.last_modified = current_time
                self.config_instance._reload_config()

class Config:
    """Enhanced Config class with file watching capabilities"""
    _instance = None
    _config_filepath: Optional[Path] = None
    _config: Dict = {}
    _count: int = 0
    _observers: List[Callable] = []
    _file_observer: Optional[Observer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._config_filepath = get_config_filepath()
            cls._setup_file_watcher(cls._instance)
            cls._instance._load_config()
        cls._count += 1
        return cls._instance

    @classmethod
    def _setup_file_watcher(cls, instance):
        """Set up the file system watcher for the config file"""
        if cls._file_observer is None:
            cls._file_observer = Observer()
            event_handler = ConfigFileHandler(instance)
            cls._file_observer.schedule(
                event_handler,
                str(cls._config_filepath.parent),
                recursive=False
            )
            cls._file_observer.start()

    def _load_config(self):
        """Load the configuration from file"""
        with open(self._config_filepath, 'r', encoding='utf-8') as file:
            try:
                self._config = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(f"Error loading config: {exc}")

    def _reload_config(self):
        """Reload the configuration and notify observers"""
        old_config = self._config.copy()
        self._load_config()

        # Notify observers of changes
        for observer in self._observers:
            try:
                observer(old_config, self._config)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def add_observer(self, callback: Callable[[Dict, Dict], None]):
        """Add an observer to be notified of config changes

        Args:
            callback: Function that takes (old_config, new_config) as arguments
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[Dict, Dict], None]):
        """Remove an observer"""
        if callback in self._observers:
            self._observers.remove(callback)

    def __getitem__(self, key):
        return self._config.get(key, None)

    def __contains__(self, key):
        return key in self._config

    def get(self, value, default=None) -> Any:
        """Get a config value with a default fallback"""
        value = self[value]
        if value is None:
            return default
        return value

    @property
    def keys(self):
        """All the elements of the config"""
        return list(self._config.keys())

    @property
    def dict(self):
        """All the elements of the config as a dict"""
        return self._config.copy()  # Return a copy to prevent direct modification

    @property
    def root(self):
        """Relative to this config.py file, the AMI root repo dir"""
        return Path(__file__).parent.parent.parent

    def __del__(self):
        """Cleanup the file observer when the config instance is destroyed"""
        if self._file_observer is not None:
            self._file_observer.stop()
            self._file_observer.join()

    #---------------- LOGGING SPECIFIC

    @property
    def log_config(self):
        """Get the logger config according to the config"""
        log_config: Dict[str, Any] = self.get("logging", {})
        return {
            "stdout": log_config.get("stdout", True),
            "save_dir": self.ai_dir / log_config.get("directory", "logs"),
            "log_level": log_config.get("level", "INFO"),
            "rotation": log_config.get("rotation", "1 day"),
            "retention": log_config.get("retention", "30 days"),
            "compression": log_config.get("compression", "gz")
        }

    #---------------- AI SPECIFIC

    @property
    def ai_dir(self):
        """Get the Path of the AI file system"""
        ai_dir_path = self.root / self["ai_filesystem"]
        ai_dir_path.mkdir(parents=True, exist_ok=True)
        return ai_dir_path

    @property
    def oww_models_dir(self) -> Path:
        """ Get the path for OWW models, create the directory if it doesn't exist """
        models_dir = self.ai_dir / "resources" / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        return models_dir

    @property
    def hot_word(self) -> str:
        """ Get the Path for the hot word file """
        return self["hot_word"]

    @property
    def headspaces_dir(self):
        """ Get the Path for the headspaces sub filesystem """
        headspaces_dir = self.ai_dir / "headspaces"
        headspaces_dir.mkdir(parents=True, exist_ok=True)
        return headspaces_dir

    @property
    def server_port(self):
        """Get the server port per the config"""
        return self.get('port')

    @property
    def server_host(self):
        """Get the host per the config"""
        return self.get('host')

    @property
    def enabled_headspaces(self) -> List[str]:
        """ Get the enabled headspaces per the config as a tuple """
        return tuple(self.get('enabled_headspaces', default=[]))

    @property
    def listening_patience(self):
        return self["listening_patience"]

    @property
    def listening_timeout(self):
        return self["listening_timeout"]

    @property
    def silence_threshold(self):
        return self["min_silence_threshold"]

    @property
    def detection_threshold(self):
        return self.get("detection_threshold", default=0.5)

#---------------- HEADSPACE SPECIFIC

    @property
    def modules_dir(self):
        """ Get the path to the add on headspace modules per the config """
        if self.get("modules_dir") is None:
            return self.root / "modules"
        return self.root / self["modules_dir"]

    def get_headspace_dir(self, headspace_name):
        core_headspaces_dir = Path(__file__).parent / "headspace" / "core"
        modular_headspace_dir = self.modules_dir

        core_path = core_headspaces_dir / headspace_name
        modular_path = modular_headspace_dir / headspace_name

        if core_path.is_dir():
            return core_path
        elif modular_path.is_dir():
            return modular_path
        else:
            return None
