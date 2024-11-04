
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer, QTime, QDate, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

class TimeDateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Time layout
        time_layout = QHBoxLayout()
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont('Arial', 24, QFont.Weight.Bold))

        self.seconds_label = QLabel()
        self.seconds_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.seconds_label.setFont(QFont('Arial', 12))

        self.ampm_label = QLabel()
        self.ampm_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.ampm_label.setFont(QFont('Arial', 12))

        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.seconds_label)
        time_layout.addWidget(self.ampm_label)

        # Date layout
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFont(QFont('Arial', 14))

        self.month_year_label = QLabel()
        self.month_year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_year_label.setFont(QFont('Arial', 12))

        layout.addLayout(time_layout)
        layout.addWidget(self.date_label)
        layout.addWidget(self.month_year_label)

        # Update time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateDateTime)
        self.timer.start(1000)

        self.updateDateTime()

    def updateDateTime(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()

        time_str = current_time.toString('hh:mm')
        seconds_str = current_time.toString(':ss')
        ampm_str = current_time.toString('AP')
        date_str = current_date.toString('dddd d')
        month_year_str = current_date.toString('MMMM yyyy')

        self.time_label.setText(time_str)
        self.seconds_label.setText(seconds_str)
        self.ampm_label.setText(ampm_str)
        self.date_label.setText(date_str)
        self.month_year_label.setText(month_year_str)
