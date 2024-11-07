
from datetime import date
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer, QTime, QDate, Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel

from ami.interfaces.gui.widgets import BaseWidget

class ClockWidget(BaseWidget):
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
