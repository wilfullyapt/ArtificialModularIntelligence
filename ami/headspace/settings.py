"""
This defines the default settings used for plugins.
If the plugin developer is smart, they will establish their own settings for their plugin to take advantage of.
This file contains all the default characteristics for how a plugin behave. Headspace, GUI, and Blueprint.
This docstring was written upon the inception of this file. I wonder at how much this will grow to govern all behavior.
"""

import json
from pathlib import Path
from typing import ClassVar, Optional, Union

from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator, model_validator

class BaseWidgetSettings(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    relx: Optional[float] = None
    rely: Optional[float] = None
    anchor: str = "nw"

    width: int = 300
    height: int = 300

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

    @field_validator("width", "height")
    @classmethod
    def validate_dimension(cls, v: Union[int, float], info: ValidationInfo) -> Union[int, float]:
        if isinstance(v, float) and not (0.0 <= v <= 1.0):
            raise ValueError(f"'{info.field_name}' as a float must be between 0.0 and 1.0, got {v}")
        if isinstance(v, int) and v <= 0:
            raise ValueError(f"'{info.field_name}' as an int must be positive, got {v}")
        return v

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

