from PyQt6.QtWidgets import QLayout, QWidgetItem
from PyQt6.QtCore import QRect, QSize, Qt
from typing import Dict, Any, List

from ami.core import LogBase

class FlexiblePositioningLayout(QLayout, LogBase):
    """
    A flexible layout manager that supports both absolute (x,y) and relative (relx,rely) positioning
    with anchor points.
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[QWidgetItem] = []
        self._positions: Dict[QWidgetItem, Dict[str, Any]] = {}

    def addWidget(self, w, x=None, y=None, relx=None, rely=None, anchor='nw', 
                 width=None, height=None):
        """Add a widget to the layout with flexible positioning options."""
        item = QWidgetItem(w)
        self._items.append(item)

        if width is not None or height is not None:
            w.setFixedSize(
                width if width is not None else w.sizeHint().width(),
                height if height is not None else w.sizeHint().height()
            )

        self._positions[item] = {
            'x': x,
            'y': y,
            'relx': relx,
            'rely': rely,
            'anchor': anchor if anchor in self.ANCHOR_OFFSETS else 'nw'
        }

        self.addChildWidget(w)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            cfg = self._positions.pop(item, None)
            return item
        return None

    def expandingDirections(self):
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical

    def hasHeightForWidth(self):
        return False

    def setGeometry(self, rect):
        super().setGeometry(rect)

        for item in self._items:
            widget = item.widget()
            if not widget or not widget.isVisible():
                continue

            cfg = self._positions.get(item, {})
            w = widget.sizeHint().width()
            h = widget.sizeHint().height()

            if cfg.get('x') is not None and cfg.get('y') is not None:
                x = cfg['x']
                y = cfg['y']
            else:
                x = int(rect.width() * (cfg.get('relx', 0)))
                y = int(rect.height() * (cfg.get('rely', 0)))

            anchor_x, anchor_y = self.ANCHOR_OFFSETS[cfg.get('anchor', 'nw')]
            x -= int(w * anchor_x)
            y -= int(h * anchor_y)

            # Keep widgets within bounds
            x = max(0, min(x, rect.width() - w))
            y = max(0, min(y, rect.height() - h))

            widget.setGeometry(QRect(x, y, w, h))

    def sizeHint(self):
        return QSize(800, 600)  # Default size hint

    def minimumSize(self):
        return QSize(0, 0)
