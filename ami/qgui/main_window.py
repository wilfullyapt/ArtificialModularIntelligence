import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFrame, 
                           QVBoxLayout, QLabel, QWidget)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor, QFont
from datetime import datetime

class TimeDisplayFrame(QFrame):
    """Custom QFrame widget for displaying time and date information"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Set frame style
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("QFrame { background-color: black; color: white; }")
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create labels with custom fonts
        self.time_label = QLabel()
        self.time_label.setFont(QFont('Arial', 48))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.date_label = QLabel()
        self.date_label.setFont(QFont('Arial', 24))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add labels to layout
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        
        # Set layout
        self.setLayout(layout)
        
        # Create timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        
        # Initial time update
        self.update_time()
        
    def update_time(self):
        current = datetime.now()
        
        # Update time (12-hour format with seconds)
        time_text = current.strftime("%I:%M:%S %p")
        self.time_label.setText(time_text)
        
        # Update date
        date_text = current.strftime("%A, %B %d")
        self.date_label.setText(date_text)

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create and add TimeDisplayFrame
        time_frame = TimeDisplayFrame()
        layout.addWidget(time_frame)
        layout.setAlignment(time_frame, Qt.AlignmentFlag.AlignTop)
        
        # Set window properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()
        
        # Hide cursor
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
        
    def keyPressEvent(self, event):
        # Press Escape to exit
        if event.key() == Qt.Key.Key_Escape:
            self.close()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
