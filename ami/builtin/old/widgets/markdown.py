from pathlib import Path

from PyQt6.QtWidgets import QTextBrowser
from PyQt6.QtCore import Qt

from . import BuildtinWidget

class MarkdownWidget(BuildtinWidget):
    """Widget that displays markdown content with support for lists, links, tables, and headers."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.render_widget()

    def render_widget(self):
        self.text_browser = QTextBrowser(self)
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setMarkdown("")
        # Apply styling from config
        style = f"""
            QTextBrowser {{
                color: {self.config.color};
                background-color: {self.config.background_color};
                border: {self.config.border_width}px solid {self.config.color};
                font-family: {self.config.font};
                font-size: {self.config.font_size}px;
                padding: 10px;
            }}
        """
        self.text_browser.setStyleSheet(style)

        # Set size based on config or default
        width = self.config.extra.get('width', 600)
        height = self.config.extra.get('height', 400)
        self.text_browser.setFixedSize(width, height)

        # Set word wrap mode
        self.text_browser.setWordWrapMode(Qt.TextOption.WrapAtWordBoundaryOrAnywhere)

    def set_markdown(self, markdown_text: str):
        """Set the markdown content to display."""
        self.text_browser.setMarkdown(markdown_text)

    def load_markdown_file(self, file_path: Path):
        """Load and display markdown content from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
            self.set_markdown(markdown_text)
        except Exception as e:
            self.logs.error(f"Error loading markdown file: {str(e)}")
            self.set_markdown(f"Error loading markdown file: {str(e)}")
