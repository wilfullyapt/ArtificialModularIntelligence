from pathlib import Path
from typing import List
from shutil import copy2 as file_copy

import markdown as md

from PyQt6.QtWidgets import QLabel, QTextBrowser, QGridLayout
from PyQt6.QtCore import Qt

from ami.headspace import BaseWidget

from .settings import MarkdownDefaultSettings

def copy_default_markdowns(destination_dir: Path):
    """Copy default markdown files to the destination directory."""
    parent_dir = Path(__file__).parent
    markdown_files = [f for f in parent_dir.glob("*.md")]
    for md_file in markdown_files:
        destination = destination_dir / md_file.name
        destination.write_bytes(md_file.read_bytes())

class MarkdownGUI(BaseWidget):        # Or QWidget if GuiFrame isn’t applicable
    """PyQt6 plugin for displaying markdown files."""
    settings_class = MarkdownDefaultSettings

    def setup_ui(self):
        """ Inherited required GUI init """
        self.setStyleSheet(f"background-color: {self.settings.background_color}; border: {self.settings.border};")
        self.screen_width = self.screen().availableSize().width()
        self.screen_height = self.screen().availableSize().height()
        self.render_markdown_files([ self.filespace / file for file in self.settings.markdown_files])
        self.logs.debug(f"MarkdownGUI has been rendered! {self.parent()}")

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
        md_text_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        md_text_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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

    def sanitize_markdown_files_and_check_existence(self, markdown_files: List[Path]) -> List[Path]:
        """ Move default markdown to the .ami directory and remove md files in the List that don't exist """
        for mdf in markdown_files:
            if not mdf.exists():
                if mdf.name in MarkdownDefaultSettings().markdown_files:
                    file_copy(Path(__file__).parent/mdf.name, mdf)
                    self.logs.info(f"Copy default markdown file: {mdf.name}")
        markdown_files = [ mdf for mdf in markdown_files if mdf.is_file() ]
        self.logs.debug(f"Markdown files being rendered: {[ mdf.name for mdf in markdown_files]}")
        return markdown_files

    def render_markdown_files(self, markdown_files):
        """Render multiple markdown files in a grid layout."""
        self.logs.info("Rendering markdown")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        total_width = 0
        markdown_files = self.sanitize_markdown_files_and_check_existence(markdown_files)
        for i, markdown_file in enumerate(markdown_files):
            md_width = self.settings.width if isinstance(self.settings.width, int) else int(self.screen_width * self.settings.width)
            total_width += md_width

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

        height = self.settings.height if isinstance(self.settings.height, int) else int(self.screen_height * self.settings.height)
        self.setFixedHeight(height)
        self.setFixedWidth(total_width)

        self.logs.debug(f"Markdown info(Frame): [ Name: {self.objectName()} , Height: {self.height()} , Width: {self.width()} ]")
