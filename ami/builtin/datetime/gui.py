import time

from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QGridLayout

from ami.gui import BaseWidget,BaseWidgetSettings 

class DateTimeDefaultSettings(BaseWidgetSettings):
    x: int = 1
    y: int = 1
    anchor: str = "nw"
    background_color: str = "black"
    font_name: str = "Arial"
    highlight_color: str = "#C3C3C3"
    lowlight_color: str = "#C3C3C3"

class DateTime(BaseWidget):
    """ The DateTime builtin Headspace GUI for the AMI project """
    settings_class = DateTimeDefaultSettings

    def update_time(self):
        self.date_label.setText(time.strftime('%A %B %d, %Y'))
        self.time_label.setText(time.strftime('%I:%M'))
        self.seconds_label.setText(time.strftime(':%S'))
        self.am_pm_label.setText(time.strftime('%p'))
    
    def setup_ui(self):
        """
        Main UI initializer
        Set up all the QLabels and Layout
        All the Labels to the Layout
        Start the timer for updating
        """
        self.setStyleSheet(f"background-color: {self.settings.background_color};")
        
        self.date_label = QLabel()
        self.date_label.setFont(QFont(self.settings.font, 26))
        self.date_label.setStyleSheet(f"color: {self.settings.highlight_color};")
        
        self.time_label = QLabel()
        self.time_label.setFont(QFont(self.settings.font, 28))
        self.time_label.setStyleSheet(f"color: {self.settings.highlight_color};")
        
        self.seconds_label = QLabel()
        self.seconds_label.setFont(QFont(self.settings.font, 18))
        self.seconds_label.setStyleSheet(f"color: {self.settings.lowlight_color};")
        
        self.am_pm_label = QLabel()
        self.am_pm_label.setFont(QFont(self.settings.font, 24))
        self.am_pm_label.setStyleSheet(f"color: {self.settings.lowlight_color};")

        layout = QGridLayout()
        layout.addWidget(self.date_label, 0, 0, 1, 3)   # row=0, col=0, rowspan=1, colspan=3
        layout.addWidget(self.time_label, 1, 0)         # row=1, col=0
        layout.addWidget(self.seconds_label, 1, 1)      # row=1, col=1
        layout.addWidget(self.am_pm_label, 1, 2)        # row=1, col=2
        
        self.time_label.setContentsMargins(0, 0, 5, 0)
        self.seconds_label.setContentsMargins(0, 0, 5, 0)
        self.am_pm_label.setContentsMargins(0, 0, 15, 0)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
