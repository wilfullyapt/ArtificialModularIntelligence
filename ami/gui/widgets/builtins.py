from pathlib import Path

from PyQt6.QtCore import QTimer, QTime, QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtSvgWidgets import QSvgWidget

from . import BuildtinWidget

class ClockWidget(BuildtinWidget):
    def __init__(self, config: dict):
        super().__init__(config)
        self.render_widget()

    def assign_settings(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            ClockWidget {{ background-color: {self.config.background_color}; color: {self.config.color}; }}
            QLabel {{ color: {self.config.color}; }}
        """)

    def render_widget(self):
        self.time_label_font = QFont(self.config.font, self.config.font_size, QFont.Weight.Bold)
        self.seconds_label_font = QFont(self.config.font, int(self.config.font_size//1.6))
        self.date_label_font = QFont(self.config.font, int(self.config.font_size//1.3))

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        time_layout = QHBoxLayout()
        time_layout.setSpacing(2)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(time_layout)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.time_label.setFont(self.time_label_font)

        self.seconds_label = QLabel()
        self.seconds_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.seconds_label.setFont(self.seconds_label_font)
        self.seconds_label.setStyleSheet("padding-bottom: 3px;")

        self.ampm_label = QLabel()
        self.ampm_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.ampm_label.setFont(self.time_label_font)

        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.seconds_label)
        time_layout.addWidget(self.ampm_label)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.date_label.setFont(self.date_label_font)

        self.month_year_label = QLabel()
        self.month_year_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_year_label.setFont(self.date_label_font)

        layout.addLayout(time_layout)
        layout.addWidget(self.date_label)
        layout.addWidget(self.month_year_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateDateTime)
        self.timer.start(1000)

        self.updateDateTime()
        self.show()

    def updateDateTime(self):

        current_time = QTime.currentTime()
        current_date = QDate.currentDate()

        if self.config.extra.get('hour_format', 12):
            time_str = current_time.toString('h:mm AP').split()[0]
            ampm_str = current_time.toString('AP')
            self.ampm_label.setText(ampm_str)
            self.ampm_label.show()
        else:
            time_str = current_time.toString('hh:mm')
            self.ampm_label.hide()

        seconds_str = current_time.toString('ss')
        date_str = current_date.toString('d dddd')
        month_year_str = current_date.toString('MMMM yyyy')

        self.time_label.setText(time_str)
        self.time_label.setFont(self.time_label_font)

        self.seconds_label.setText(seconds_str)
        self.seconds_label.setFont(self.seconds_label_font)

        self.date_label.setText(date_str)
        self.date_label.setFont(self.date_label_font)

        self.month_year_label.setText(month_year_str)
        self.month_year_label.setFont(self.date_label_font)


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

class NotificationStack(BuildtinWidget):
    """ Specific set of icon indicators for notifications and updates
        Includes:
            - Timer functions
            - Wifi connection
            - Automations
            - Messages from Headspaces
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.DEFAULT_ICONS = [ 'hourglass', 'automations', 'ai', 'wifi' ]

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
#       return self.config.extra.get('icons', self.DEFAULT_ICONS)

    def get_icon(self, icon) -> NotificationIcon:
        icon_path = Path(__file__).parent.parent / "resources"  / f"{icon}.svg"

        if not icon_path.parent.is_dir():
            self.logs.critical(f"Icon resource directory not found: {icon_path}")
            raise NotADirectoryError(f"Icon resource directory not found: {icon_path}")
        if not icon_path.exists() and icon_path:
            self.logs.critical(f"Icon SVG resource not found: {icon_path}")
            raise FileNotFoundError(f"Icon SVG resource not found: {icon_path}")

        return NotificationIcon(icon_path, icon, self.icon_size)
