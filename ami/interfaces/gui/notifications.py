from pathlib import Path
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import Qt, QTimer

from ami.interfaces.gui.widgets import BaseWidget

DEFAULT_ICONS = [ 'hourglass', 'automations', 'ai', 'wifi' ]

class NotificationIcon(QWidget):
    """ Visual that displays an SVG icon with an optional message/count indicator """

    def __init__(self, svg_path: Path, name: str, size: int, parent=None):
        super().__init__(parent)
        self.name = name
        self.message = ""
        self.count = 0
        self.pulse_opacity = 1.0
        self.pulse_growing = False

        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        self.svg_widget = QSvgWidget(str(svg_path.resolve()))
        self.svg_widget.setFixedSize(size, size)
        layout.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Message Label
        self.message_label = QLabel()
        self.message_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setFixedWidth(60)
        layout.addWidget(self.message_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("""
            QLabel {
                background-color: #FF5722;
                color: white;
                border-radius: 8px;
                padding: 2px 4px;
                font-size: 10px;
            }
        """)
        self.count_label.hide()
        layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

        # Setup pulse animation timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50)  # 50ms interval for smooth animation

    def set_message(self, message):
        """Set temporary message below the icon"""
        self.message = message
        self.message_label.setText(message)
        self.message_label.setVisible(bool(message))

    def set_count(self, count):
        """Set count indicator"""
        self.count = count
        self.count_label.setText(str(count))
        self.count_label.setVisible(count > 0)

    def update_pulse(self):
        """Update pulse animation"""
        if self.pulse_growing:
            self.pulse_opacity += 0.05
            if self.pulse_opacity >= 1.0:
                self.pulse_opacity = 1.0
                self.pulse_growing = False
        else:
            self.pulse_opacity -= 0.05
            if self.pulse_opacity <= 0.3:
                self.pulse_opacity = 0.3
                self.pulse_growing = True

        self.svg_widget.setStyleSheet(f"opacity: {self.pulse_opacity};")

class NotificationStack(BaseWidget):
    """ Specific set of icon indicators for notifications and updates
        Includes:
            - Timer functions
            - Wifi connection
            - Automations
            - Messages from Headspaces
    """

    def __init__(self, config: dict):
        super().__init__(config)

        self.setWindowTitle("Top Right Icon Stack")
#       self.setGeometry(100, 100, 400, 400)

        self.icon_layout = QVBoxLayout()
        self.icon_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._icons = {}
        for icon in self.icons:
            icon = self.get_icon(icon)
            self.icon_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
            self._icons[icon.name] = icon

        self.setLayout(self.icon_layout)

    @property
    def icon_size(self):
        return self.config.extra.get('icon_size', 40)

    @property
    def icon_padding(self):
        return self.config.extra.get('icon_padding', 10)

    @property
    def icons(self):
        return ['hourglass', 'automations']
#       return self.config.extra.get('icons', DEFAULT_ICONS)

    def get_icon(self, icon) -> NotificationIcon:
        icon_path = Path(__file__).parent / "resources"  / f"{icon}.svg"

        if not icon_path.parent.is_dir():
            self.logs.critical(f"Icon resource directory not found: {icon_path}")
            raise NotADirectoryError(f"Icon resource directory not found: {icon_path}")
        if not icon_path.exists() and icon_path:
            self.logs.critical(f"Icon SVG resource not found: {icon_path}")
            raise FileNotFoundError(f"Icon SVG resource not found: {icon_path}")

        return NotificationIcon(icon_path, icon, self.icon_size)
