""" Core functionality for Artificial Modular Intelligence """

from .config import Config
from .logger import LoggerConfig, Logger, Base as LogBase
<<<<<<< HEAD
from .registry import PluginRegistry
from .watcher import ConfigMetadataPluginWatcher
=======
from .registry import PluginRegistry, PluginVertical
from .watcher import ConfigMetadataPluginWatcher
from .conversation import Conversation
>>>>>>> convostate

__all__ = [
    "Config",
    "LoggerConfig",
    "Logger",
    "LogBase",
    "PluginRegistry",
<<<<<<< HEAD
    "ConfigMetadataPluginWatcher",
=======
    "PluginVertical",
    "ConfigMetadataPluginWatcher",
    "Conversation"
>>>>>>> convostate
]
