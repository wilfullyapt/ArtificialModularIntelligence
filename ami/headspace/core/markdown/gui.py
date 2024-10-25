import re
from pathlib import Path
from tkinter import Label, Text, END
from typing import List

import markdown as md
from pydantic import BaseModel, Field

from ami.headspace.gui import GuiFrame

def default_markdowns(destination_dir: Path):
    parent_dir = Path(__file__).parent
    markdown_files = [f for f in parent_dir.glob("*.md")]

    for md_file in markdown_files:
        destination = destination_dir / md_file.name
        destination.write_bytes(md_file.read_bytes())

class FontSettings(BaseModel):
    font: str = Field(default="Verdana")
    font_size: int = Field(default=12)
    h1_size: int = Field(default=22)
    h2_size: int = Field(default=20)
    h3_size: int = Field(default=18)

class Markdown(GuiFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.screen_width = self.winfo_screenwidth()
        self.config(bg='black', borderwidth=0)

    def load_settings(self):
        config_markdown_files: List[str] = self.yaml.get("files")
        self.markdown_files = [ self.filesystem / filename for filename in config_markdown_files ]

        font_settings_dict = {k.replace('-', '_'): v for k, v in self.yaml.get("font-settings", {}).items()}
        self.font_settings = FontSettings(**font_settings_dict)
        self.side_padding = self.yaml.get("padding", 20)

        column_width = self.screen_width // len(self.markdown_files)
        self.column_width = min(column_width, self.yaml.get('width', 300))
        self.md_height = self.yaml.get('height', 300)
        self.text_width = self.column_width // (self.font_settings.font_size // 2)
        self.logs.debug(f"Markdown settings: max_width={column_width}, set_width={self.column_width}, text_width={self.text_width}, height={self.md_height}, padding: {self.side_padding}")

        if not all(file.exists() for file in self.markdown_files):
            default_markdowns(self.filesystem.path)

    def define_render(self) -> None:
        self.load_settings()
        self.render_markdown_files(self.markdown_files)

    def render_markdown_files(self, markdown_files):
        self.configure(width=self.column_width*len(markdown_files), height=self.md_height)
        self.pack_propagate(False)
        self.grid_propagate(False)

        for i, markdown_file in enumerate(markdown_files):
            md_name = Label(
                self,
                text=markdown_file.name,
                font=(self.font_settings.font, 20, "bold"),
                relief="solid",
                borderwidth=2,
                highlightthickness=2,
                highlightbackground="white",
                highlightcolor="white",
                anchor='center'
            )
            md_widget = self.render_markdown_file(markdown_file)

            self.grid_columnconfigure(i, weight=1, minsize=self.column_width)
            md_name.grid(row=0, column=i, sticky='nsew', padx=self.side_padding, pady=4)
            md_widget.grid(row=1, column=i, sticky='nsew', padx=self.side_padding)
            md_widget.config(width=self.text_width, height=self.md_height)

        self.grid_rowconfigure(1, weight=1)

        self.logs.debug(f"Markdown info(Frame): [ Name: {self.winfo_name()} , Height: {self.winfo_height()} , Width: {self.winfo_width()} ]")

    def get_markdown_from_path(self, markdown_filepath: Path):
        with markdown_filepath.open('r') as f:
            return f.read()

    def get_html_from_markdown_path(self, markdown_filepath: Path):
        return md.markdown(self.get_markdown_from_path(markdown_filepath))

    def render_markdown_file(self, markdown_file: Path):
        md_text_widget = Text(
            self,
            wrap='word',
            bg='black',
            fg='white',
            padx=0,
            pady=0,
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            width=self.text_width
        )

        md_text_widget.tag_configure("h1", font=(self.font_settings.font, self.font_settings.h1_size), foreground="red")
        md_text_widget.tag_configure("h2", font=(self.font_settings.font, self.font_settings.h2_size), foreground="orange")
        md_text_widget.tag_configure("h3", font=(self.font_settings.font, self.font_settings.h3_size), foreground="yellow")
        md_text_widget.tag_configure("bold", font=(self.font_settings.font, self.font_settings.font_size, "bold"))
        md_text_widget.tag_configure("italic", font=(self.font_settings.font, self.font_settings.font_size, "italic"))
        md_text_widget.tag_configure("list", font=(self.font_settings.font, self.font_settings.font_size), foreground="white")

        numbered_list = False
        list_counter = 0

        for line in self.get_html_from_markdown_path(markdown_file).split('\n'):
            if line.startswith('<h1>'):
                md_text_widget.insert(END, '\n')
                md_text_widget.insert(END, line[4:-5] + '\n', 'h1')
            elif line.startswith('<h2>'):
                md_text_widget.insert(END, '\n')
                md_text_widget.insert(END, line[4:-5] + '\n', 'h2')
            elif line.startswith('<h3>'):
                md_text_widget.insert(END, '\n')
                md_text_widget.insert(END, line[4:-5] + '\n', 'h3')
            elif line.startswith('<ul>'):
                pass
            elif line.startswith('<ol>'):
                md_text_widget.insert(END, line[4:-5] + '\n', 'list')
                numbered_list = True
                list_counter = 1
            elif line.startswith('</ul>') or line.startswith('</ol>'):
                numbered_list = False

            elif line.startswith('<li>'):
                if numbered_list:
                    md_text_widget.insert(END, f'{list_counter}. ' + line[4:-5] + '\n', 'list')
                    list_counter += 1
                else:
                    md_text_widget.insert(END, '• ' + line[4:-5] + '\n', 'list')
            else:
                parts = re.split(r'(<strong>|</strong>|<em>|</em>)', line)
                current_tag = ''
                for part in parts:
                    if part == '<strong>':
                        current_tag = 'bold'
                    elif part == '</strong>':
                        current_tag = ''
                    elif part == '<em>':
                        current_tag = 'italic'
                    elif part == '</em>':
                        current_tag = ''
                    else:
                        md_text_widget.insert(END, part, current_tag)
                md_text_widget.insert(END, '\n')
        return md_text_widget

