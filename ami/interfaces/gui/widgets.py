from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass, field

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from ami.base import Base

class WidgetAlignment(Enum):
    TOP = Qt.AlignmentFlag.AlignTop
    BOTTOM = Qt.AlignmentFlag.AlignBottom
    LEFT = Qt.AlignmentFlag.AlignLeft
    RIGHT = Qt.AlignmentFlag.AlignRight
    CENTER = Qt.AlignmentFlag.AlignHCenter
    MIDDLE = Qt.AlignmentFlag.AlignVCenter

    TOP_LEFT = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
    TOP_CENTER = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
    TOP_RIGHT = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
    MIDDLE_LEFT = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
    MIDDLE_CENTER = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter
    MIDDLE_RIGHT = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
    BOTTOM_LEFT = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
    BOTTOM_CENTER = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
    BOTTOM_RIGHT = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight

@dataclass
class WidgetConfig:
    enabled: bool = True
    font: str = "Arial"
    font_size: int = 12
    alignment: str = "top|left"
    color: str = "#000000"
    background_color: str = "#FFFFFF"
    border_width: int = 0

    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def _convert_kebab_to_snake(key: str) -> str:
        """Convert kebab-case to snake_case."""
        return key.replace('-', '_')

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WidgetConfig':
        """Create a WidgetConfig instance from a dictionary."""

        converted_dict = {
            cls._convert_kebab_to_snake(k): v 
            for k, v in config_dict.items()
        }

        known_params = {
            k: v for k, v in converted_dict.items() 
            if k in cls.__dataclass_fields__ and k != 'extra'
        }

        extra_params = {
            k: v for k, v in converted_dict.items()
            if k not in cls.__dataclass_fields__
        }

        return cls(**known_params, extra=extra_params)

class BaseWidget(QWidget, Base):
    """Base widget class with configuration management."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = WidgetConfig.from_dict(config)
        self._setup_widget()

    def _setup_widget(self):
        """Initialize widget based on configuration."""
        try:

            self.setEnabled(self.config.enabled)

            style = f"""
                QWidget {{
                    color: {self.config.color};
                    background-color: {self.config.background_color};
                    border: {self.config.border_width}px solid {self.config.color};
                    font-family: {self.config.font};
                    font-size: {self.config.font_size}px;
                }}
            """
#           self.setStyleSheet(style)

        except Exception as e:
            self.logs.error(f"Error setting up widget: {str(e)}")


    def _parse_alignment(self, alignment_str: str) -> Qt.AlignmentFlag:
        """Parse an alignment string into Qt alignment flags."""
        alignment_str = alignment_str.upper().replace(' ', '_')

        if '|' in alignment_str:
            parts = alignment_str.split('|')
            compound_key = f"{parts[0]}_{parts[1]}"
            try:
                return WidgetAlignment[compound_key].value
            except KeyError:
                self.logs.warn(f"Invalid compound alignment '{compound_key}', using TOP_LEFT")
                return WidgetAlignment.TOP_LEFT.value

        try:
            return WidgetAlignment[alignment_str].value
        except KeyError:
            self.logs.warn(f"Invalid alignment '{alignment_str}', using TOP_LEFT")
            return WidgetAlignment.TOP_LEFT.value

    @property
    def alignment(self) -> Qt.AlignmentFlag:
        """Convert alignment string to Qt alignment flags."""
        return self._parse_alignment(self.config.alignment)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """ Get a configuration value, checking both standard and extra parameters. """
        if hasattr(self.config, key):
            return getattr(self.config, key)
        return self.config.extra.get(key, default)
