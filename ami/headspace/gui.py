""" GUI Abstract Base Class

This module defines an abstract base class for creating GUI frames in a tkinter application.
It provides a foundation for building modular and configurable GUI components.

The GuiFrame class serves as a base for creating custom frames with standardized
initialization, rendering, and configuration loading capabilities. It also includes
error handling for invalid placements and missing configurations.

Classes:
    MissingConfigException: Custom exception for missing configuration files.
    InvalidPlacementError: Custom exception for invalid widget placements.
    GuiFrame: Abstract base class for GUI frames.

The module relies on tkinter for GUI components and uses YAML for configuration management.
"""

import json
import os
import sys
from pathlib import Path
from functools import cached_property
from typing import ClassVar, Dict, Any, Optional, Type

from PyQt6.QtWidgets import QWidget
from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator, model_validator

from ami.core import Config
from ami.headspace import Primitive


class BaseWidgetSettings(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    relx: Optional[float] = None
    rely: Optional[float] = None
    anchor: str = "nw"

    background_color: str = "black"
    font: str = "Arial"
    highlight_color: str = "#C3C3C3"
    lowlight_color: str = "#C3C3C3"

    VALID_ANCHORS: ClassVar[set[str]] = {
        "nw",     "n",     "ne",
        "w",   "center",   "e",
        "sw",     "s",     "se"
    }

    @field_validator("anchor")
    @classmethod
    def validate_anchor(cls, v):
        if v not in cls.VALID_ANCHORS:
            raise ValueError(f"Anchor must be one of {cls.VALID_ANCHORS}, got '{v}'")
        return v

    @field_validator("relx", "rely")
    @classmethod
    def validate_relative_range(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError(f"'{info.field_name}' must be between 0.0 and 1.0, got {v}")
        return v

    @model_validator(mode='after')
    def check_positioning(self) -> 'BaseWidgetSettings':
        has_absolute = self.x is not None and self.y is not None
        has_relative = self.relx is not None and self.rely is not None

        if has_absolute and has_relative:
            raise ValueError("Cannot specify both absolute (x, y) and relative (relx, rely) positioning")
        if not has_absolute and not has_relative:
            raise ValueError("Must specify either absolute (x, y) or relative (relx, rely) positioning")

        return self

    def save_to_file(self, file_path: Path) -> None:
        with open(file_path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_file(cls, file_path: Path) -> 'BaseWidgetSettings':
        if file_path.is_file():
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    return cls(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"Warning: Invalid settings file '{file_path}', using defaults: {e}")
                settings = cls()
                settings.save_to_file(file_path)
                return settings
        else:
            settings = cls()
            settings.save_to_file(file_path)
            return settings

class BaseWidget(QWidget, Primitive):
    """
    Base widget class with configuration management. settings_class must be defined by the child.

    """
    settings_class: Type[BaseWidgetSettings] = None

    def __init__(self, parent: Optional[QWidget] = None):
        QWidget.__init__(self, parent)
        if self.settings_class is None:
            raise ValueError("Subclasses must define 'settings_class'")
        self.setup_ui()

    def __init_subclass__(cls, **kwargs):
        """ Called when a subclass is defined. Sets the plugin_directory attribute on the subclass. """
        super().__init_subclass__(**kwargs)
        file_path = sys.modules[cls.__module__].__file__
        directory = os.path.basename(os.path.dirname(file_path))
        cls.plugin_directory = directory

    @cached_property
    def filespace(self) -> Path:
        filespace = Config().plugin_data_dir / self.__class__.plugin_directory
        filespace.mkdir(parents=True, exist_ok=True)
        return filespace

    @cached_property
    def name(self) -> str:
        return self.__class__.__name__

    @cached_property
    def _settings_file(self) -> Path:
        return self.filespace /  f"{self.name}_settings.json"

    @cached_property
    def settings(self) -> type[BaseWidgetSettings]:
        return self._load_settings()

    @property
    def placement(self) -> Dict[str, Any]:
        """
        Returns a dictionary with positioning information based on settings.
        Returns either absolute (x, y, anchor) or relative (relx, rely, anchor) positioning.
        """
        if self.settings.relx is not None and self.settings.rely is not None:
            return {
                'relx': self.settings.relx,
                'rely': self.settings.rely,
                'anchor': self.settings.anchor
            }
        return {
            'x': self.settings.x,
            'y': self.settings.y,
            'anchor': self.settings.anchor
        }

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

    def setup_ui(self) -> None:
        raise NotImplementedError("Subclasses must implement 'setup_ui'")
