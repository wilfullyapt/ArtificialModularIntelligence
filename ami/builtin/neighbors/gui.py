"""Thin GUI widget listing local vs internet AMI neighbors."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout

from ami.headspace import BaseWidget

from .settings import NeighborsSettings


class NeighborsGUI(BaseWidget):
    """Builtin Neighbors headspace GUI."""

    settings_class = NeighborsSettings
    main_view = True

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Neighbors")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setFont(QFont(self.settings.font, 16))
        title.setStyleSheet(f"color: {self.settings.highlight_color}; background: transparent;")

        body = QLabel(
            "Local mesh peers and optional internet neighbors.\n"
            "Ask AMI: list neighbors · announce presence · mesh status"
        )
        body.setWordWrap(True)
        body.setFont(QFont(self.settings.font, 11))
        body.setStyleSheet(f"color: {self.settings.lowlight_color}; background: transparent;")

        layout.addWidget(title)
        layout.addWidget(body)
        layout.addStretch(1)
        self.setStyleSheet(f"background-color: {self.settings.background_color};")
