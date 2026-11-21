""" Core functionality for Artificial Modular Intelligence """

from __future__ import annotations

from typing import Any

from .config import Config
from .logger import LoggerConfig, Logger, Base as LogBase
from .conversation import Conversation
from .interaction import InteractionStore, SpanKind, SpanStatus, TurnReceipt

__all__ = [
    "Config",
    "LoggerConfig",
    "Logger",
    "LogBase",
    "PluginRegistry",
    "PluginVertical",
    "Plugin",
    "ConfigMetadataPluginWatcher",
    "Conversation",
    "InteractionStore",
    "TurnReceipt",
    "SpanKind",
    "SpanStatus",
    "ConfigUpdater",
]


def __getattr__(name: str) -> Any:
    if name in ("PluginRegistry", "PluginVertical", "Plugin"):
        from . import registry as _registry

        return getattr(_registry, name)
    if name == "ConfigMetadataPluginWatcher":
        from .watcher import ConfigMetadataPluginWatcher as _W

        return _W
    if name == "ConfigUpdater":
        from .utils import ConfigUpdater as _CU

        return _CU
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
