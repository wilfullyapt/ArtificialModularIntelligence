"""Popup dialog for AMI interaction"""
from enum import Enum
from typing import Callable, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget, QScrollArea

from ..core import LogBase

class Dialog(QWidget, LogBase):
    """Widget representing a single message in the conversation"""
    def __init__(self, parent, speaker: str, message: str, loading: bool=False):
        QWidget.__init__(self, parent)
        LogBase.__init__(self)

        speaker = speaker.upper()
        self._is_loading = loading
        self._spinner_sprites = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
        self._spinner_idx = 0
        self.base_message = message
        self._id = id(self)
        self.destroyed.connect(self._on_destroyed)

        self.message_layout = QHBoxLayout()
        self.message_layout.setContentsMargins(0, 5, 0, 5)

        self.speaker_label = QLabel(speaker)
        self.speaker_label.setFixedWidth(80)
        self.speaker_label.setStyleSheet("color: #4CAF50;" if speaker == "HUMAN" else "color: #2196F3;")

        self.message_label = QLabel(self._get_message_text())
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: white;")

        # Main vertical layout
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(self.message_layout)
        self.main_layout.addWidget(self.speaker_label)
        self.main_layout.addWidget(self.message_label, stretch=1)
        self.setLayout(self.main_layout)

        self._spinner_timer = QTimer()
        self._spinner_timer.timeout.connect(self._update_spinner)
        if self._is_loading:
            self._spinner_timer.start(100)

    def _get_message_text(self) -> str:
        """Get the current display text including spinner if loading"""
        if self._is_loading:
            return f"{self.base_message} {self._spinner_sprites[self._spinner_idx]}"
        return self.base_message

    def _update_spinner(self):
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_sprites)
        self.message_label.setText(self._get_message_text())

    def get_speaker(self) -> str:
        """Return the speaker of this message"""
        return self.speaker_label.text()

    def get_message(self) -> str:
        """Return the message text"""
        return self.message_label.text()

    def update_message(self, new_text: str, is_loading: bool=False):
        """Update the message text"""
        if self._is_loading and not is_loading and self._spinner_timer.isActive():
            self._spinner_timer.stop()
        self._is_loading = is_loading
        self.message_label.setText(new_text)

    def inject_widget(self, w: QWidget):
        self.main_layout.addWidget(w)

    def _on_destroyed(self):
        """Handle the destroyed signal"""
        self.logs.info(f"Dialog destroyed: ID={self._id}, Speaker={self.get_speaker()}, Message='{self.base_message}'")

    def deleteLater(self):
        if self._spinner_timer.isActive():
            self._spinner_timer.stop()
        self.logs.info(f"Delete called on {str(self)}")
        QWidget.deleteLater(self)

class ConversationView(QScrollArea, LogBase):
    """Scrollable container for conversation messages"""
    def __init__(self, parent=None):
        QScrollArea.__init__(self, parent)
        LogBase.__init__(self)
        self.messages = []

        # UI setup
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_layout = QVBoxLayout()
        self.messages_layout.setSpacing(0)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.addStretch()

        content_widget = QWidget()
        content_widget.setLayout(self.messages_layout)
        self.setWidget(content_widget)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
            QScrollArea {
                border: 1px solid red;
                background: transparent;
            }
            QWidget {
                background: transparent;
                border: none;
            }
        """)

    def __getitem__(self, index: int) -> Dialog|None:
        """ Get Dialog in self.messages by index """
        try:
            return self.messages[index]
        except Exception as e:
            self.logs.error(f"Error in index retrieval for ConverstationView.messages(index={index}): {e}")
            return None

    def append_message(self, speaker: str, message: str, with_loading: bool=True):
        """Add a new message to the conversation"""
        msg_widget = Dialog(self, speaker, message, loading=with_loading)
        self.messages.append(msg_widget)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg_widget)
        self.logs.debug(f"Added Message: {speaker}: {message}")
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def update_last_message(self, speaker: str, new_text: str) -> bool:
        """
        Update the last message from the specified speaker.
        Return True if checks pass or False with an error if failed.
        """
        dialog = self[-1]
        if isinstance(dialog, Dialog):
            if dialog.get_speaker() == speaker:
                dialog.update_message(new_text)
                self.logs.debug(f"Message Updated: {speaker}: {new_text}")
                return True
            else:
                self.logs.error(f"Incorrect speaker passed to ConversationView(). {speaker} instead of {dialog.get_speaker()}")
                return False
        else:
            self.logs.error(f"Dialog is of the wrong type: type({type(dialog)})")
            return False

    def inject_inline_widget(self, w:QWidget):
        dialog = self[-1]
        if isinstance(dialog, Dialog):
            dialog.inject_widget(w)

    def reset(self):
        """Reset the conversation by clearing all messages and widgets"""

        while self.messages_layout.count() > 1:         # Leave the stretch item
            item = self.messages_layout.takeAt(0)       # Remove from top (before stretch)
            widget = item.widget()              # item.widget() returns a QWidget (if the item is a widget)
            if widget:                          #   or None if it isn't a QWidget
                if isinstance(widget, Dialog):  # Check if the widget is a Dialog object
                    widget.deleteLater()        # Destroy the Dialog Widget
                else:
                    self.logs.warning(          # Issues a warning if an unexpected widget appears
                        f"Unexpected widget in ConversationView: type={type(widget)}, "
                        f"object={str(widget)}, parent={widget.parent()}"
                    )
                    widget.deleteLater()        # Delete the Dialog widget
            else:
                self.logs.error("Unexpected non-widget item found in layout before stretch")

        self.messages.clear()               # Reset the messages list

class DialogSize(Enum):
    MAX = "MAX"
    MIN = "MIN"

class ConversationState(Enum):
    """States for the conversation popup"""
    IDLE = "IDE"
    LISTENING = "LISTENING"
    HUMAN_SPEAKING = "HUMAN_SPEAKING"
    AI_THINKING = "AI_THINKING"
    AI_RESPONDING = "AI_RESPONDING"

class AMIDialog(QDialog, LogBase):
    """Popup dialog for AMI interaction"""
    def __init__(self, parent=None, timeout_callback: Optional[Callable]=None):
        QDialog.__init__(self, parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.timeout_callback = timeout_callback
        self.state = ConversationState.IDLE

        # Get screen size from parent
        if self.parent():
            screen_size = self.parent().screen().size()

            self.initial_width = screen_size.width() // 2   # Set init size width to 1/2 and height 1/3
            self.initial_height = screen_size.height() // 3

            self.max_width = screen_size.width() - 20       # Set maximum size to screen size minus margins
            self.max_height = screen_size.height() - 20

            self.setMinimumSize(self.initial_width, self.initial_height)
            self.resize(self.initial_width, self.initial_height)
            self.setMaximumSize(self.max_width, self.max_height)

        self.setStyleSheet("""
            QDialog {
                background-color: black;
                border: 2px solid white;
                border-radius: 3px;
            }
            QProgressBar {
                border: none;
                background: #333333;
                height: 9px;
                margin: 2px;
            }
            QProgressBar::chunk {
                background: #666666;
            }
#           QWidget { border: 1px solid red; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.conversation = ConversationView(self)
        layout.addWidget(self.conversation)

        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self._update_progress)
        self.close_timer.setInterval(50)

    def _update_progress(self):
        """Update progress bar and check for auto-close"""
        current = self.progress_bar.value()
        if current > 0:
            self.progress_bar.setValue(current - 50)
        else:
            self.close_timer.stop()
            self.close()
            self.state = ConversationState.IDLE

    def center_on_parent(self):
        """Center dialog on parent window"""
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2
            )

    def show_listening(self):
        """Show listening state"""
        assert self.state is ConversationState.IDLE

        self.logs.debug("Listening started!")

        self.state = ConversationState.LISTENING
        self.progress_bar.setValue(0)
        self.conversation.append_message("HUMAN", "Listening")
        self.center_on_parent()
        self.show()

    def show_transcription(self, text: str):
        """Show transcription and AI thinking state"""
        assert self.state is ConversationState.LISTENING

        self.conversation.update_last_message("HUMAN", text)
        self.conversation.append_message("AI", "Thinking")

        self.state = ConversationState.AI_THINKING

    def show_response(self, text: str):
        """Show AI response and start auto-close timer"""
        assert self.state is ConversationState.AI_THINKING

        self.state = ConversationState.AI_RESPONDING
        self.conversation.update_last_message("AI", text)

        self.progress_bar.setMaximum(10000)
        self.progress_bar.setValue(10000)
        self.close_timer.start()

    def append_widget_inline(self, w: QWidget):
        if self.state == ConversationState.AI_RESPONDING:
            self.conversation.inject_inline_widget(w)
        else:
            self.logs.error(f"Failure trying to append widget[{w}] to the popup conversation")

    def closeEvent(self, event):
        """Handle cleanup on close"""
        if self.close_timer.isActive():
            self.close_timer.stop()
        self.progress_bar.setValue(0)

        self.conversation.reset()

        self.state = ConversationState.IDLE

        if self.timeout_callback: self.timeout_callback()
        super().closeEvent(event)
