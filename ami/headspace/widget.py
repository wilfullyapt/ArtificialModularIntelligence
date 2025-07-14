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

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QWidget

from ..headspace import Primitive

ANCHOR_OFFSETS = {
        'nw': (0, 0),           # Top-left (default)
        'n': (0.5, 0),          # Top-center
        'ne': (1, 0),           # Top-right
        'w': (0, 0.5),          # Mid-left
        'center': (0.5, 0.5),   # Center
        'e': (1, 0.5),          # Mid-right
        'sw': (0, 1),           # Bottom-left
        's': (0.5, 1),          # Bottom-center
        'se': (1, 1),           # Bottom-right
    }

class BaseWidget(QWidget, Primitive):
    """ Base widget class with configuration management """

    main_view = True

    def __init__(self, parent: Optional[QWidget] = None):
        QWidget.__init__(self, parent)
        self.hide()
        self._setup_ui()
        self._w: int = self.settings.width
        self._h = self.settings.height
        self.internal_rect: Optional[QRect] = None

    @property
    def w(self):
        return self._w
    @property
    def h(self):
        return self._h
    def set_width(self, width: int):
        self._w = width
    def set_height(self, height: int):
        self._h = height

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

    def _setup_ui(self) -> None:
        self.setup_ui()
        self.setFixedSize(self.sizeHint())

    def show(self) -> None:
        if self.main_view:
            QWidget.show(self)

    def resizeEvent(self, event):
        self.logs.debug(f"BaseWidget resize Event: {event}")
        self.a= event
        QWidget.resizeEvent(self, event)

    def setGeometry(self, rect: QRect) -> None:
        QWidget.setGeometry(self, rect)
        self.logs.debug(f"BaseWidget[{self.name}].setGeometry({rect}) called")

    def setGeometry_new(self, rect: QRect) -> None:
        """
        Sets the plugin widget's geometry based on the rect of the parent (ami.gui.layouts)
        Widget geometry is based on the settins x, y, relx, rely, and anchor.
        """
        w = self.sizeHint().width()
        h = self.sizeHint().height()

        cfg = self.placement

        if 'x' in cfg and 'y' in cfg and cfg['x'] is not None and cfg['y'] is not None:
            x = cfg['x']
            y = cfg['y']
        else:
            x = int(rect.width() * cfg.get('relx', 0))
            y = int(rect.height() * cfg.get('rely', 0))

        anchor = cfg.get('anchor', 'nw')
        anchor_x, anchor_y = ANCHOR_OFFSETS.get(anchor, (0, 0))
        x -= int(w * anchor_x)
        y -= int(h * anchor_y)

        x = max(0, min(x, rect.width() - w))
        y = max(0, min(y, rect.height() - h))

        new_rect = QRect(x, y, w, h)
        if new_rect == self.internal_rect:
            self.logs.debug(f"setGeometry call not necessary for {self.name}")
        else:
            QWidget.setGeometry(self, new_rect)
            self.logs.debug(f"BaseWidget[{self.name}].setGeometry({new_rect}) called")
