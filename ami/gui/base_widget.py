from functools import cached_property
import json
from pathlib import Path
from typing import ClassVar, Dict, Any, Optional, Tuple, Type
from dataclasses import dataclass, field

from PyQt6.QtWidgets import QWidget
from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator

from ami.core import LogBase, Config


class BaseWidgetSettings(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    relx: Optional[float] = None
    rely: Optional[float] = None
    anchor: str = "nw"
    background_color: str = "black"
    font_name: str = "Arial"
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

    @field_validator("x", "y", "relx", "rely")
    @classmethod
    def validate_positioning(cls, v: Any, info: ValidationInfo) -> Any:
        # Get current field values from info.data
        data = info.data
        has_absolute = data.get("x") is not None or data.get("y") is not None or (info.field_name in ("x", "y") and v is not None)
        has_relative = data.get("relx") is not None or data.get("rely") is not None or (info.field_name in ("relx", "rely") and v is not None)

        # Ensure exactly one positioning method is used
        if has_absolute and has_relative:
            raise ValueError("Cannot specify both absolute (x, y) and relative (relx, rely) positioning")
        if not has_absolute and not has_relative:
            raise ValueError("Must specify either absolute (x, y) or relative (relx, rely) positioning")

        # Ensure pairs are complete
        if info.field_name == "x" and v is not None and "y" not in data and info.field_name != "y":
            raise ValueError("If 'x' is specified, 'y' must also be specified")
        if info.field_name == "y" and v is not None and "x" not in data and info.field_name != "x":
            raise ValueError("If 'y' is specified, 'x' must also be specified")
        if info.field_name == "relx" and v is not None and "rely" not in data and info.field_name != "rely":
            raise ValueError("If 'relx' is specified, 'rely' must also be specified")
        if info.field_name == "rely" and v is not None and "relx" not in data and info.field_name != "relx":
            raise ValueError("If 'rely' is specified, 'relx' must also be specified")

        # Validate relative positioning ranges
        if info.field_name in ("relx", "rely") and v is not None:
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"'{info.field_name}' must be between 0.0 and 1.0, got {v}")
        return v

    def save_to_file(self, file_path: Path) -> None:
        with open(file_path, "w") as f:
            f.write(self.model_dump_json())

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

class BaseWidget(QWidget, LogBase):
    """
    Base widget class with configuration management. settings_class must be defined by the child.

    """
    settings_class: Type[BaseWidgetSettings] = None

    def __init__(self, parent: Optional[QWidget] = None):
        QWidget.__init__(parent)
        if self.settings_class is None:
            raise ValueError("Subclasses must define 'settings_class'")
        self.setup_ui()

    @cached_property
    def _settings_file(self) -> Path:
        return Config().data_dir /  f"{self.__class__.__name__}.json"

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
                    return self.settings_class(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"Warning: Invalid settings file '{self._settings_file}', using defaults: {e}")
                settings = self.settings_class()
                settings.save_to_file(self._settings_file)
                return settings
        else:
            settings = self.settings_class()
            settings.save_to_file(self._settings_file)
            return settings

    def setup_ui(self) -> None:
        raise NotImplementedError("Subclasses must implement 'setup_ui'")
