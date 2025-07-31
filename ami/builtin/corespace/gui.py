import time
from datetime import datetime

from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton

from ami.headspace import BaseWidget

from .settings import CorespaceSettings 
from .tool import ReminderManager, UpdateManager

class CorespaceGUI(BaseWidget):
    """GUI component for corespace with reminder notifications"""
    
    settings_class = CorespaceSettings
    reminder_updated = pyqtSignal()
    dom = None

    def setup_ui(self):
        """Initialize the GUI components"""

        self.setStyleSheet(f"""
            background-color: {self.settings.background_color}; 
            font-family: {self.settings.font_family};
        """)
        
        # Initialize managers
        self.reminder_manager = ReminderManager(self.filespace, self.settings.reminder_files)
        self.update_manager = UpdateManager()

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Current date
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFont(QFont(self.settings.font, 24))
        self.date_label.setStyleSheet(f"color: {self.settings.highlight_color};")
        layout.addWidget(self.date_label)
        
        # Current time
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont(self.settings.font, 28))
        self.time_label.setStyleSheet(f"color: {self.settings.highlight_color}; margin-bottom: 10px")
        layout.addWidget(self.time_label)
        
        # Reminder notifications area
        self.reminder_area = QVBoxLayout()
        layout.addLayout(self.reminder_area)
        
        self.setLayout(layout)
        
        # Setup timers
        self.setup_timers()
        
        # Initial updates
        self.update_time()
        self.update_reminders()
    
    def setup_timers(self):
        """Setup periodic timers for updates"""
        # Timer for clock updates (every second)
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)
        
        # Timer for reminder checks
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.update_reminders)
        self.reminder_timer.start(self.settings.polling_interval_seconds * 1000)
        
        # Timer for recurring reminder processing (every 5 minutes)
        self.recurring_timer = QTimer()
        self.recurring_timer.timeout.connect(self.process_recurring_reminders)
        self.recurring_timer.start(5 * 60 * 1000)  # 5 minutes
    
    def update_date(self):
        """ Update the current date display """
        now = datetime.now()
        self.dom = now.day
        date_text = now.strftime("%A, %B %d, %Y")
        self.date_label.setText(date_text)

    def update_time(self):
        """ Update the current time display """
        now = datetime.now()
        if self.dom != now.day:
            self.update_date()
        time_text = now.strftime("%I:%M:%S %p")
        self.time_label.setText(time_text)
    
    def update_reminders(self):
        """Update reminder notifications"""
        try:
            # Clear existing reminder widgets
            while self.reminder_area.count():
                child = self.reminder_area.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Get upcoming reminders
            upcoming = self.reminder_manager.get_upcoming_reminders(
                self.settings.notification_threshold_hours
            )
            
            if upcoming:
                reminder_title = QLabel("Upcoming Reminders:")
                reminder_title.setFont(QFont(self.settings.font_family, 12, QFont.Weight.Bold))
                reminder_title.setStyleSheet("color: #ffcc00; margin: 5px 0;")
                self.reminder_area.addWidget(reminder_title)
                
                for reminder in upcoming:
                    self.create_reminder_widget(reminder)
            
        except Exception as e:
            self.logs.error(f"Error updating reminders: {e}")
    
    def create_reminder_widget(self, reminder):
        """Create a widget for displaying a reminder"""
        container = QHBoxLayout()
        
        # Reminder text
        reminder_label = QLabel(reminder['message'])
        reminder_label.setFont(QFont(self.settings.font_family, 10))
        reminder_label.setWordWrap(True)
        
        # Time remaining
        time_left = reminder['time_left']
        if time_left.total_seconds() > 0:
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            time_text = f"{hours:02d}:{minutes:02d}"
        else:
            time_text = "OVERDUE"
        
        time_label = QLabel(time_text)
        time_label.setFont(QFont(self.settings.font_family, 12, QFont.Weight.Bold))
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setMinimumWidth(80)
        
        # Style based on urgency
        if reminder.get('is_urgent', False) or time_left.total_seconds() <= 0:
            bg_color = self.settings.reminder_background_color
            text_color = "black"
        else:
            bg_color = "#2a2a2a"
            text_color = "white"
        
        reminder_label.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            padding: 5px;
            border-radius: 3px;
            margin: 2px;
        """)
        
        time_label.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            padding: 5px;
            border-radius: 3px;
            margin: 2px;
            font-weight: bold;
        """)
        
        # Complete button
        complete_btn = QPushButton("✓")
        complete_btn.setMaximumWidth(30)
        complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        complete_btn.clicked.connect(
            lambda checked, text=reminder['original_text']: self.complete_reminder(text)
        )
        
        container.addWidget(reminder_label, 1)
        container.addWidget(time_label)
        container.addWidget(complete_btn)
        
        # Create a widget to hold the layout
        reminder_widget = QVBoxLayout()
        reminder_widget.addLayout(container)
        self.reminder_area.addLayout(reminder_widget)
    
    def complete_reminder(self, reminder_text):
        """Mark a reminder as completed"""
        try:
            success = self.reminder_manager.complete_reminder(reminder_text)
            if success:
                self.update_reminders()  # Refresh display
        except Exception as e:
            self.logs.error(f"Error completing reminder: {e}")
    
    def process_recurring_reminders(self):
        """Process recurring reminders"""
        try:
            self.reminder_manager.process_recurring_reminders()
            self.update_reminders()  # Refresh display after processing
        except Exception as e:
            self.logs.error(f"Error processing recurring reminders: {e}")
    
    def check_updates(self):
        """Check for system updates"""
        try:
            result = self.update_manager.check_for_updates()
            if result['update_available']:
                self.update_button.setText("Update Available - Click to Update")
                self.update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #ff8c00;
                        color: black;
                        border: 1px solid #ff6600;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff9900;
                    }
                """)
                self.update_button.clicked.disconnect()
                self.update_button.clicked.connect(self.perform_update)
            else:
                self.update_button.setText("System Up to Date")
                self.update_button.setEnabled(False)
        except Exception as e:
            self.logs.error(f"Error checking updates: {e}")
            self.update_button.setText("Update Check Failed")
    
    def perform_update(self):
        """Perform system update"""
        try:
            self.update_button.setText("Updating...")
            self.update_button.setEnabled(False)
            
            result = self.update_manager.perform_update()
            if result['success']:
                self.update_button.setText("Update Complete - Restart Required")
                self.update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: 1px solid #45a049;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
            else:
                self.update_button.setText("Update Failed")
                self.update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: 1px solid #da190b;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
        except Exception as e:
            self.logs.error(f"Error performing update: {e}")
            self.update_button.setText("Update Error")
