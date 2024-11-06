from PyQt6.QtWidgets import QWidget
from typing import Optional, Dict, Any
import logging

class FlexiblePositioningLayout(QWidget):
    """
    A flexible layout manager that supports both absolute (x,y) and relative (relx,rely) positioning
    with anchor points. Absolute positioning takes precedence over relative positioning.

    Key differences from QStackedLayout:
    - QStackedLayout is for stacking widgets on top of each other, showing one at a time (like a deck of cards)
    - This layout is for precise positioning of multiple visible widgets
    """

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

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._widgets: Dict[QWidget, Dict[str, Any]] = {}

    def add_widget(self, 
                  widget: QWidget,
                  x: Optional[int] = None,
                  y: Optional[int] = None,
                  relx: Optional[float] = None,
                  rely: Optional[float] = None,
                  anchor: str = 'nw',
                  width: Optional[int] = None,
                  height: Optional[int] = None) -> None:
        """
        Add a widget to the layout with flexible positioning options.

        Args:
            widget: The widget to position
            x: Absolute x coordinate (takes precedence over relx)
            y: Absolute y coordinate (takes precedence over rely)
            relx: Relative x position (0-1)
            rely: Relative y position (0-1)
            anchor: Anchor point ('nw', 'n', 'ne', 'w', 'center', 'e', 'sw', 's', 'se')
            width: Fixed width for the widget
            height: Fixed height for the widget
        """
        if anchor not in self.ANCHOR_OFFSETS:
            logging.warning(f"Invalid anchor '{anchor}', defaulting to 'nw'")
            anchor = 'nw'

        self._widgets[widget] = {
            'x': x,
            'y': y,
            'relx': relx,
            'rely': rely,
            'anchor': anchor,
            'width': width,
            'height': height
        }

        widget.setParent(self)
        if width is not None or height is not None:
            widget.setFixedSize(
                width if width is not None else widget.sizeHint().width(),
                height if height is not None else widget.sizeHint().height()
            )

        self.update_widget_geometry(widget)

    def update_widget_geometry(self, widget: QWidget) -> None:
        """Update a widget's position and size based on its configuration."""
        if widget not in self._widgets:
            return

        cfg = self._widgets[widget]

        w = cfg['width'] if cfg['width'] is not None else widget.sizeHint().width()
        h = cfg['height'] if cfg['height'] is not None else widget.sizeHint().height()

        if cfg['x'] is not None and cfg['y'] is not None:
            # Use absolute positioning
            x = cfg['x']
            y = cfg['y']
        else:
            # Use relative positioning
            x = int(self.width() * (cfg['relx'] or 0))
            y = int(self.height() * (cfg['rely'] or 0))

        anchor_x, anchor_y = self.ANCHOR_OFFSETS[cfg['anchor']]
        x -= int(w * anchor_x)
        y -= int(h * anchor_y)

        widget.setGeometry(x, y, w, h)

    def resizeEvent(self, event):
        """Handle resize events by updating all widget positions."""
        for widget in self._widgets:
            self.update_widget_geometry(widget)
