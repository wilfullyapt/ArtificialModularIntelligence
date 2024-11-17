from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget, QScrollArea

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

        # Message label
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: white;")

        layout.addWidget(self.role_label)
        layout.addWidget(self.message_label, 1)

    def setText(self, text: str):
        self.message_label.setText(text)

class AMIDialog(QDialog):
    """Main dialog for AMI interaction"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        # Set up the main dialog
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QDialog {
                background: #1a1a1a;
                border: 1px solid #666666;
                border-radius: 5px;
            }
        """)

        # Initial size
        self.normal_size = QRect(0, 0, 500, 700)
        self.expanded_size = QRect(0, 0, 800, 1000)
        self.setGeometry(self.normal_size)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

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
        self.message_container.setStyleSheet("background: transparent;")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.message_container)

        self.main_layout.addWidget(self.scroll_area)

        # Loading animation
        self.dot_animation = DotAnimation()
        self.dot_animation.hide()

        # Timer for countdown
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)

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

    def hide_with_animation(self):
        """Hide dialog with fade-out animation"""
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.close)
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

    def start_listening(self):
        """Initialize listening state"""
        message_widget = MessageWidget("HUMAN")
        message_widget.setText("Listening...")
        self.message_layout.addWidget(message_widget)
        self.dot_animation.show()
        self.dot_animation.start()
        self.show_with_animation()

    def show_human_message(self, text: str):
        """Display human message"""
        self.dot_animation.stop()
        self.dot_animation.hide()

        # Update or add message widget
        message_widget = self.message_layout.itemAt(self.message_layout.count() - 1).widget()
        if isinstance(message_widget, MessageWidget) and message_widget.role_label.text() == "HUMAN":
            message_widget.setText(text)
        else:
            message_widget = MessageWidget("HUMAN")
            message_widget.setText(text)
            self.message_layout.addWidget(message_widget)

    def prepare_ai_response(self):
        """Show thinking animation for AI"""
        message_widget = MessageWidget("AI")
        message_widget.setText("Thinking...")
        self.message_layout.addWidget(message_widget)
        self.dot_animation.show()
        self.dot_animation.start()

    def show_ai_message(self, text: str, expand: bool = False):
        """Display AI message and optionally expand dialog"""
        self.dot_animation.stop()
        self.dot_animation.hide()

        if expand:
            self.expand(True)

        # Update or add message widget
        message_widget = self.message_layout.itemAt(self.message_layout.count() - 1).widget()
        if isinstance(message_widget, MessageWidget) and message_widget.role_label.text() == "AI":
            message_widget.setText(text)
        else:
            message_widget = MessageWidget("AI")
            message_widget.setText(text)
            self.message_layout.addWidget(message_widget)

        # Start countdown
        self.start_countdown()

    def start_countdown(self, duration: int = 10):
        """Start the countdown timer"""
        self.progress_bar.setMaximum(duration * 1000)  # milliseconds
        self.progress_bar.setValue(duration * 1000)
        self.countdown_timer.start(50)  # Update every 50ms

    def update_countdown(self):
        """Update the countdown progress"""
        current = self.progress_bar.value()
        if current > 0:
            self.progress_bar.setValue(current - 50)
        else:
            self.countdown_timer.stop()
            self.hide_with_animation()

    def keyPressEvent(self, event):
        """Prevent dialog from closing on Escape key"""
        if event.key() != Qt.Key.Key_Escape:
            super().keyPressEvent(event)
