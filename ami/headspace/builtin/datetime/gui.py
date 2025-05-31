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

    def setup_ui(self):
        pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "datetime"
        
        # Set background color
        self.setStyleSheet(f"background-color: {self.settings.background_color};")
        
        # Create labels
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
        
        # Setup layout
        self.define_render()
        
        # Setup timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 1000ms
    
    def update_time(self):
        self.date_label.setText(time.strftime('%A %B %d, %Y'))
        self.time_label.setText(time.strftime('%I:%M'))
        self.seconds_label.setText(time.strftime(':%S'))
        self.am_pm_label.setText(time.strftime('%p'))
    
    def define_render(self):
        layout = QGridLayout()
        
        # Add widgets to layout
        layout.addWidget(self.date_label, 0, 0, 1, 3)   # row=0, col=0, rowspan=1, colspan=3
        layout.addWidget(self.time_label, 1, 0)         # row=1, col=0
        layout.addWidget(self.seconds_label, 1, 1)      # row=1, col=1
        layout.addWidget(self.am_pm_label, 1, 2)        # row=1, col=2
        
        # Set alignment and padding
        self.time_label.setContentsMargins(0, 0, 5, 0)
        self.seconds_label.setContentsMargins(0, 0, 5, 0)
        self.am_pm_label.setContentsMargins(0, 0, 15, 0)
        
        self.setLayout(layout)
        
        # Initial update
        self.update_time()
