import re
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QLabel, QTextBrowser, QGridLayout
from PyQt6.QtCore import Qt
from typing import List
import markdown as md
from pydantic import BaseModel, Field, ValidationError

# Replace with your base class if not using GuiFrame
from ami.gui.base_widget import BaseWidget, BaseWidgetSettings
from ami.headspace.gui import GuiFrame  # Assuming this exists in your project

def copy_default_markdowns(destination_dir: Path):
    """Copy default markdown files to the destination directory."""
    parent_dir = Path(__file__).parent
    markdown_files = [f for f in parent_dir.glob("*.md")]
    for md_file in markdown_files:
        destination = destination_dir / md_file.name
        destination.write_bytes(md_file.read_bytes())

class MarkdownDefaultSettings(BaseWidgetSettings):
    relx: float = .5
    rely: float = .4
    anchor: str = "n"
    markdown_files: List[str] = ["effective_accelerationism.md", "techno_optimist.md"]
    background_color: str = "black"
    border: str = "none"
    font_name: str = "Arial"
    highlight_color: str = "#C3C3C3"
    lowlight_color: str = "#C3C3C3"

    width: int = 300
    height: int = 300
    padding: int = 20

    font: str = "Verdana"
    font_size: int = 12
    h1_size: int = 22
    h2_size: int = 20
    h3_size: int = 18

class MarkdownGUI(BaseWidget):        # Or QWidget if GuiFrame isn’t applicable
    """PyQt6 plugin for displaying markdown files."""

    settings_class = MarkdownDefaultSettings

    def setup_ui(self):
        pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "Markdown"
        self.setStyleSheet(f"background-color: {self.settings.background_color}; border: {self.settings.border};")
        self.screen_width = self.screen().availableSize().width()

    def define_render(self) -> None:
        self.render_markdown_files([ self.filespace / file for file in self.settings.markdown_files])

    def render_markdown_files(self, markdown_files):
        """Render multiple markdown files in a grid layout."""
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for i, markdown_file in enumerate(markdown_files):
            # Create and style the file name label
            md_name = QLabel(markdown_file.name)
            md_name.setStyleSheet(f"""
                font-family: {self.settings.font};
                font-size: 20px;
                font-weight: bold;
                border: 2px solid white;
                padding: 4px;
                color: white;
            """)
            md_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Render markdown content
            md_widget = self.render_markdown_file(markdown_file)

            # Add widgets to layout
            layout.addWidget(md_name, 0, i, 1, 1)
            layout.addWidget(md_widget, 1, i, 1, 1)

            # Configure column properties
            layout.setColumnMinimumWidth(i, self.settings.width)
            layout.setColumnStretch(i, 1)

        # Allow the content row to expand
        layout.setRowStretch(1, 1)

        self.setLayout(layout)
        self.setFixedHeight(self.settings.height)

        self.logs.debug(f"Markdown info(Frame): [ Name: {self.objectName()} , Height: {self.height()} , Width: {self.width()} ]")

    def get_markdown_from_path(self, markdown_filepath: Path) -> str:
        """Read markdown content from a file."""
        with markdown_filepath.open('r') as f:
            return f.read()

    def get_html_from_markdown_path(self, markdown_filepath: Path) -> str:
        """Convert markdown content to HTML."""
        return md.markdown(self.get_markdown_from_path(markdown_filepath))

    def render_markdown_file(self, markdown_file: Path) -> QTextBrowser:
        """Render a single markdown file as styled HTML."""
        md_text_widget = QTextBrowser()
        md_text_widget.setStyleSheet("""
            background-color: black;
            color: white;
            border: none;
        """)
        md_text_widget.setReadOnly(True)
        md_text_widget.setHtml(self.get_html_from_markdown_path(markdown_file))

        # Apply custom CSS for styling
        css = f"""
        h1 {{ font-family: {self.settings.font}; font-size: {self.settings.h1_size}px; color: red; }}
        h2 {{ font-family: {self.settings.font}; font-size: {self.settings.h2_size}px; color: orange; }}
        h3 {{ font-family: {self.settings.font}; font-size: {self.settings.h3_size}px; color: yellow; }}
        strong {{ font-family: {self.settings.font}; font-size: {self.settings.font_size}px; font-weight: bold; }}
        em {{ font-family: {self.settings.font}; font-size: {self.settings.font_size}px; font-style: italic; }}
        li {{ font-family: {self.settings.font}; font-size: {self.settings.font_size}px; color: white; }}
        """
        md_text_widget.document().setDefaultStyleSheet(css)

        return md_text_widget
