from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget, QScrollArea
from numpy import size

class DotAnimation(QWidget):
    """Animated dot pattern for loading states"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 20)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.dot_pos = 0
        self.dots = [False] * 3  # 3 dots that will animate

    def start(self):
        self.timer.start(300)  # Update every 300ms

    def stop(self):
        self.timer.stop()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Update dot states
        self.dots = [False] * 3
        self.dots[self.dot_pos] = True
        self.dot_pos = (self.dot_pos + 1) % 3

        # Draw dots
        pen = QPen(QColor('white'))
        painter.setPen(pen)
        for i, active in enumerate(self.dots):
            if active:
                painter.setBrush(QColor('white'))
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(10 + i*15, 5, 8, 8)

class ModernProgressBar(QProgressBar):
    """Custom progress bar with smooth animation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #333333;
                height: 4px;
            }
            QProgressBar::chunk {
                background: #666666;
            }
        """)

class MessageWidget(QWidget):
    """Widget for displaying a single message"""
    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Role label with fixed width
        self.role_label = QLabel(role)
        self.role_label.setFixedWidth(80)
        self.role_label.setStyleSheet(f"""
            color: {'#4CAF50' if role == 'HUMAN' else '#2196F3'};
            font-weight: bold;
        """)

        # Message container for text and dots
        self.message_container = QWidget()
        message_layout = QHBoxLayout(self.message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)

        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: white;")
        
        # Add dot animation widget
        self.dot_animation = DotAnimation()
        self.dot_animation.hide()

        message_layout.addWidget(self.message_label)
        message_layout.addWidget(self.dot_animation)
        message_layout.addStretch()

        layout.addWidget(self.role_label)
        layout.addWidget(self.message_container, 1)

    def setText(self, text: str, show_dots: bool = False):
        self.message_label.setText(text)
        if show_dots:
            self.dot_animation.show()
            self.dot_animation.start()
        else:
            self.dot_animation.stop()
            self.dot_animation.hide()

class AMIDialog(QDialog):
    """Main dialog for AMI interaction"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_animations()
        self.is_active = False

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.setStyleSheet("""
            QDialog {
                background-color: black;
                border: 2px solid white;
                border-radius: 5px;
            }
            QScrollArea, QWidget#message_container {
                background-color: black;
            }
            QProgressBar {
                border: none;
                background: #333333;
                height: 4px;
                margin: 2px;  /* Add margin to keep progress bar away from border */
            }
            QProgressBar::chunk {
                background: #666666;
            }
        """)

        # Initial size
        self.normal_size = QRect(0, 0, 500, 700)
        self.expanded_size = QRect(0, 0, 800, 1000)
        self.setGeometry(self.normal_size)

        # Main layout - Add padding to account for the border
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(0)

        # Progress bar
        self.progress_bar = ModernProgressBar()
        self.main_layout.addWidget(self.progress_bar)

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Container for messages
        self.message_container = QWidget()
        self.message_container.setObjectName("message_container")
        self.message_container.setStyleSheet("background: transparent;")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.message_container)

        self.main_layout.addWidget(self.scroll_area)

        # Timer for countdown
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)

    def cleanup_session(self):
        """Clean up the current session state"""
        self.countdown_timer.stop()
        self.is_active = False

        # Clean up all message widgets
        while self.message_layout.count():
            widget = self.message_layout.takeAt(0).widget()
            if isinstance(widget, MessageWidget):
                widget.cleanup()
            widget.deleteLater()

        # Reset progress bar
        self.progress_bar.setValue(0)

    def start_listening(self):
        """Initialize listening state"""
        # Clean up any existing session
        self.cleanup_session()

        # Set active state
        self.is_active = True

        # Create new message widget
        message_widget = MessageWidget("HUMAN")
        message_widget.setText("Listening...", show_dots=True)
        self.message_layout.addWidget(message_widget)

        # Show dialog with animation
        self.show_with_animation()

    def show_human_message(self, text: str):
        """Display human message"""
        if not self.is_active:
            return

        message_widget = self.message_layout.itemAt(self.message_layout.count() - 1).widget()
        if isinstance(message_widget, MessageWidget) and message_widget.role_label.text() == "HUMAN":
            message_widget.setText(text, show_dots=False)
        else:
            message_widget = MessageWidget("HUMAN")
            message_widget.setText(text, show_dots=False)
            self.message_layout.addWidget(message_widget)

    def prepare_ai_response(self):
        """Show thinking animation for AI"""
        if not self.is_active:
            return

        message_widget = MessageWidget("AI")
        message_widget.setText("Thinking...", show_dots=True)
        self.message_layout.addWidget(message_widget)

    def show_ai_message(self, text: str, expand: bool = False):
        """Display AI message and optionally expand dialog"""
        if not self.is_active:
            return

        if expand:
            self.expand(True)

        message_widget = self.message_layout.itemAt(self.message_layout.count() - 1).widget()
        if isinstance(message_widget, MessageWidget) and message_widget.role_label.text() == "AI":
            message_widget.setText(text, show_dots=False)
        else:
            message_widget = MessageWidget("AI")
            message_widget.setText(text, show_dots=False)
            self.message_layout.addWidget(message_widget)

        # Start countdown
        self.start_countdown()

    def start_countdown(self, duration: int = 10):
        """Start the countdown timer"""
        if not self.is_active:
            return

        self.countdown_timer.stop()  # Stop any existing countdown
        self.progress_bar.setMaximum(duration * 1000)
        self.progress_bar.setValue(duration * 1000)
        self.countdown_timer.start(50)

    def update_countdown(self):
        """Update the countdown progress"""
        if not self.is_active:
            self.countdown_timer.stop()
            return

        current = self.progress_bar.value()
        if current > 0:
            self.progress_bar.setValue(current - 50)
        else:
            self.countdown_timer.stop()
            self.is_active = False
            self.hide_with_animation()

    def hide_with_animation(self):
        """Hide dialog with fade-out animation"""
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.cleanup_on_hide)
        self.opacity_animation.start()

    def cleanup_on_hide(self):
        """Cleanup after hide animation completes"""
        self.close()
        self.cleanup_session()



    def setup_animations(self):
        # Size animation
        self.size_animation = QPropertyAnimation(self, b"geometry")
        self.size_animation.setDuration(300)
        self.size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Opacity animation
        self.setWindowOpacity(0.0)
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200)

    def show_with_animation(self):
        """Show dialog with fade-in animation"""
        self.center_on_parent()
        self.show()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def center_on_parent(self):
        """Center the dialog on the parent window"""
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2
            )

    def expand(self, expanded: bool = True):
        """Expand or contract the dialog"""
        target_geometry = self.expanded_size if expanded else self.normal_size

        # Ensure dialog stays centered
        if self.parent():
            parent_rect = self.parent().geometry()
            target_geometry.moveCenter(parent_rect.center())

        self.size_animation.setStartValue(self.geometry())
        self.size_animation.setEndValue(target_geometry)
        self.size_animation.start()

    def keyPressEvent(self, event):
        """Prevent dialog from closing on Escape key"""
        if event.key() != Qt.Key.Key_Escape:
            super().keyPressEvent(event)
