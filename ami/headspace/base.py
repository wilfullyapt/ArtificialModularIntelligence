""" Foundational to Headspace """

import json
import os
import sys
from functools import cached_property
from pathlib import Path
from typing import Any, Type

from pydantic import ValidationError

from ..core import LogBase, Config
from .settings import BaseWidgetSettings

class Primitive(LogBase):
    """
    Primitive is the parent class for all plugin components. Blueprint, GUI, and Headspace.
    Primitive provides the following attributes so the plugin components knows about themselves in the grand scheme.
        - Plugin Name: self.plugin_name is a proxy for self._hs_name
        - self.filespace is the directory path for the Headspace to use as filestorage
    One of the features is no __init__ method, thus not requiring super() from childen classes, works out of box
    """

    settings_class: Type[BaseWidgetSettings] = BaseWidgetSettings

    def __new__(cls, *args, **kwargs):
        """ This class is only inheritable, cannot be instantiated alone """
        if cls is Primitive:
            raise TypeError("Primitive class cannot be instantiated directly.")
        return super().__new__(cls, *args, **kwargs)

    def __init_subclass__(cls, **kwargs):
        """ Called when a subclass is defined. Sets the plugin_directory attribute on the subclass. Vibe coded. """
        super().__init_subclass__(**kwargs)
        file_path = sys.modules[cls.__module__].__file__
#       cls._hs_name = os.path.dirname(file_path)
        cls._hs_name = os.path.basename(os.path.dirname(file_path))
#       self.logs.debug(f"Primitive loaded for {cls.__module__} for Headspace {self._hs_name}")

    @cached_property
    def filespace(self) -> Path:
        filespace = Config().plugin_data_dir / self.__class__._hs_name
        filespace.mkdir(parents=True, exist_ok=True)
        return filespace

    @cached_property
    def class_name(self) -> str:
        return self.__class__.__name__.lower()

    @cached_property
    def name(self) -> str:
        return self._hs_name

    @cached_property
    def _settings_file(self) -> Path:
        return self.filespace /  f"{self.name}_settings.json"

    def _load_settings(self) -> Any:
        if self._settings_file.is_file():
            try:
                with open(self._settings_file, "r") as f:
                    data = json.load(f)
                    settings = self.settings_class(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"Warning: Invalid settings file '{self._settings_file}', using defaults: {e}")
                settings = self.settings_class()
                settings.save_to_file(self._settings_file)
        else:
            settings = self.settings_class()
            settings.save_to_file(self._settings_file)

        return settings

    @cached_property
    def settings(self) -> type[BaseWidgetSettings]:
        return self._load_settings()
