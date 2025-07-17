from typing import Dict, Any, List, Type

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtWidgets import QApplication, QLayout, QWidgetItem

from ..core import LogBase
from ..headspace.widget import BaseWidget

class ManagedFlexiblePositioningLayout(QLayout, LogBase):
    """
    A self-managed flexible layout manager.
    - Supports both absolute (x,y) and relative (relx,rely) positioning with anchor points.
    - Manages children via reloading and named indexing.
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

    def __init__(self, screen_geometry: QRect):
        QLayout.__init__(self)
        self.screen_geometry = screen_geometry
        self._managed_children: Dict[str, BaseWidget] = {}
        self._items: List[QWidgetItem] = []
        self._positions: Dict[BaseWidget, Dict[str, Any]] = {}

    def __contains__(self, managed_widget_name: str):
        return managed_widget_name in self._managed_children

    def __getitem__(self, managed_widget_name: str):
        return self._managed_children.get(managed_widget_name)

    def addItem(self, item):
        self._items.append(item)

    def addWidget(self, w, x=None, y=None, relx=None, rely=None, anchor='nw', 
                  width=None, height=None):
        """Add a widget to the layout with flexible positioning options."""
        self.addChildWidget(w)
        item = QWidgetItem(w)
        self.addItem(item)

        if width is not None or height is not None:
            w.setFixedSize(
                width if width is not None else w.sizeHint().width(),
                height if height is not None else w.sizeHint().height()
            )

        self._positions[w] = {
            'x': x,
            'y': y,
            'relx': relx,
            'rely': rely,
            'anchor': anchor if anchor in self.ANCHOR_OFFSETS else 'nw'
        }

    def add_plugin_widget(self, widget_class: Type[BaseWidget]):
        """Add a plugin widget to the layout and register it by name."""
        new_widget = widget_class()
        if new_widget.name in self._managed_children:
            self.logs.warning(f"Widget {new_widget.name} already exists, skipping.")
        else:
            new_widget.setObjectName(new_widget.name)
            self._managed_children[new_widget.name] = new_widget
            self.addWidget(new_widget, **new_widget.placement)
            new_widget.show()
            self.logs.info(f"Added widget {new_widget.name} with placement {new_widget.placement}")

    def update_plugin_widget(self, name: str):
        """Update an existing widget with a new instance."""
        if name in self._managed_children:
            old_widget = self._managed_children.pop(name)
            self.removeWidget(old_widget)
            old_widget.setParent(None)
            old_widget.destroyed.connect(lambda: self.logs.debug(f"Descructor connection: Widget {name} was destroyed"))
            old_widget.deleteLater()


            widget_class = type(old_widget)
            new_widget = widget_class(self.parent())
            self._managed_children[name] = new_widget
            self.addWidget(new_widget, **new_widget.placement)
            new_widget.show()
            self.logs.info(f"Updated widget {name}")
        else:
            self.logs.info(f"Widget {name} not found.")

    def delete_plugin_widget(self, name: str):
        """Delete a widget by plugin name from the layout and its parent."""
        if name in self._managed_children:
            dead_widget_walking = self._managed_children.pop(name)
            self.removeWidget(dead_widget_walking)
            dead_widget_walking.deleteLater()
            self.logs.debug(f"Deleted the '{name}' widget.")

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            widget = item.widget()
            if widget in self._positions:
                del self._positions[widget]
            return item
        return None

    def expandingDirections(self):
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical

    def hasHeightForWidth(self):
        return False

    def resizeEvent(self, event):
        self.logs.debug(f"IPCQWidget resize Event: {event}")
        self.a= event
#       QLayout.resizeEvent(self, event)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.logs.debug("Set geometry called on the layout")
        for item in self._items:
            widget = item.widget()
            if widget:
                cfg = self._positions.get(widget, {})
                w = widget.sizeHint().width()
                h = widget.sizeHint().height()

                if cfg.get('x') is not None and cfg.get('y') is not None:
                    x = cfg['x']
                    y = cfg['y']
                else:
                    x = int(rect.width() * cfg.get('relx', 0))
                    y = int(rect.height() * cfg.get('rely', 0))

                anchor_x, anchor_y = self.ANCHOR_OFFSETS[cfg.get('anchor', 'nw')]
                x -= int(w * anchor_x)
                y -= int(h * anchor_y)

                x = max(0, min(x, rect.width() - w))
                y = max(0, min(y, rect.height() - h))

                widget.setGeometry(QRect(x, y, w, h))

    def sizeHint(self):
        self.logs.debug("Layout.sizeHint called!")
        return self.screen_geometry.size()

    def minimumSize(self):
        self.logs.debug("Layout.minimumSize called!")
        return self.screen_geometry.size()
