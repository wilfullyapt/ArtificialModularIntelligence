from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass, field

from PyQt6.QtWidgets import QWidget

from ami.base import Base, Primitive

@dataclass
class WidgetConfig:
    enabled: bool = False
    font: str = "Arial"
    font_size: int = 12
    alignment: str = "top|left"
    color: str = "#000000"
    background_color: str = "#FFFFFF"
    border_width: int = 0

    x: int = 0
    y: int = 0
    anchor: str = 'nw'
    relflag: bool = False
    relx: float = 0.0
    rely: float = 0.0

    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def placement(self) -> dict:
        if self.relflag:
            return { 'relx': self.relx, 'rely': self.rely, 'anchor': self.anchor }
        else:
            return { 'x': self.x, 'y': self.y, 'anchor': self.anchor }

    @staticmethod
    def _convert_kebab_to_snake(key: str) -> str:
        """Convert kebab-case to snake_case."""
        return key.replace('-', '_')

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WidgetConfig':
        """Create a WidgetConfig instance from a dictionary."""

        if 'x' not in config_dict and 'y' not in config_dict:
            config_dict['relflag'] = True

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

class BuildtinWidget(QWidget, Base):
    """Base widget class with configuration management."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = WidgetConfig.from_dict(config)

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

    @property
    def placement(self) -> dict:
        return self.config.placement


class HeadspaceMeta(type(QWidget), ABCMeta):
    """
    Custom metaclass that combines Qt's metaclass with ABC's metaclass.
    This resolves the metaclass conflict between QWidget and ABC.
    """
    pass

class HeadspaceWidget(QWidget, ABC, Primitive, metaclass=HeadspaceMeta):

    def __init__(self):
        QWidget.__init__(self)
        Primitive.__init__(self)
        self.headspace = self.__module__.split('.')[-2]

    @abstractmethod
    def render_widget(self) -> None:
        """ Abstract method that defines the content of the widget """
        raise NotImplementedError("Subclasses must implement the render_widget method.")

    @property
    def placement(self):
        return self.yaml.get('placement', {'relx': 0.5, 'rely': 0.1, 'anchor': 'n'})

    def is_valid(self):
        """ Run an internal check to validate the integrity of subclassed widget """
        return True
