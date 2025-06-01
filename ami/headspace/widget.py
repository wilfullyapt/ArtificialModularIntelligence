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

from typing import Dict, Any, Optional

from PyQt6.QtWidgets import QWidget

from ami.headspace import Primitive

class BaseWidget(QWidget, Primitive):
    """ Base widget class with configuration management """

    def __init__(self, parent: Optional[QWidget] = None):
        QWidget.__init__(self, parent)
        self.setup_ui()

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


    def setup_ui(self) -> None:
        raise NotImplementedError("Subclasses must implement 'setup_ui'")
