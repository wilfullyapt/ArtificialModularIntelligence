import os
import qrcode
import yaml
import markdown
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from ami.headspace.filesystem import Filesystem
from ami.config import Config
from ami.headspace.base import SharedTool

def convert_md_to_html(md_file):
    with open(md_file, 'r') as f:
        md_content = f.read()
        html_content = markdown.markdown(md_content)
        return html_content

def get_markdown_file(filename):
    filepath = str(Config().headspaces_dir / "markdown" / filename)
    return convert_md_to_html(filepath)

class MarkdownFile(BaseModel):
    filepath: Path
    list_name: str = Field(None, description="Optional name of the target list within the markdown file")
    list_contents: List[str] = Field(default_factory=list, description="List of elements in the specific list_name")
    header_lineno: int = Field(None, description="The line number the header is at in the markdown file")

    @property
    def name(self):
        return self.filepath.name

    @property
    def headspace_location(self):
        return self.name

    @property
    def full(self):
        if self.list_name and self.list_contents:
            return True
        return

    def exists(self):
        return self.filepath.is_file()

    def get_lists(self):
        """ Returns a list of all headers that are in place as list names """
        if not self.exists():
            raise FileNotFoundError(f"The file '{self.name}' does not exist.")

        with self.filepath.open("r", encoding="utf-8") as file:
            heading_found = False
            lists = []
            for _, line in enumerate(file):

                if line.startswith("#") and line.lstrip("#")[0] == " ":
                    possible_list = line.lstrip("#").strip()
                    heading_found = True
                    continue

                if heading_found:
                    if line.startswith("- "):
                        lists.append(possible_list)
                    heading_found = False

            return lists

    def contains_list(self, list_name:str):
        """ Function only looks for headings '#' and records list elements directly under the heading """
        if not self.exists():
            raise FileNotFoundError(f"The file '{self.name}' does not exist.")

        return_flag = False
        with self.filepath.open("r", encoding="utf-8") as file:
            heading_found = False
            for i, line in enumerate(file):

                if line.startswith("#") and line.lstrip("#")[0] == " ":
                    # Special check, must be a header and not a `#hashtag`
                    if line.lstrip("#").strip() == list_name:
                        heading_found = True
                        return_flag = True
                        self.list_name = list_name
                        self.header_lineno = i
                        continue
                    else:
                        heading_found = False

                if heading_found:
                    if line.startswith("- "):
                        self.list_contents.append(line[2:].rstrip())
                    else:
                        heading_found = False

        return return_flag

class Markdown(SharedTool):
    """ Markdown has access to all markdown files likes Calendar has access to ./calendar.json

        TODO
         - Should be able to return paths of markdown files
         - Should be able to return contents of markdown files
         - Should be able to update markdown files

    """

    def __init__(self):
        local_config_path = Path(__file__).parent / "config.yaml"
        with open(local_config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.filesystem = Filesystem("markdown")

        if self.md_files == []:
            default_markdowns(self.filesystem.path)

    @property
    def md_files(self):
        return [ filename for filename in self.filesystem.contents if filename.endswith(".md") ]

    @property
    def lists(self):
        md_lists = []
        for md in [ MarkdownFile(filepath=(self.filesystem/md_file)) for md_file in self.md_files ]:
            md_lists.extend(md.get_lists())
        return md_lists

    @property
    def qr_dir(self):
        dir_path = Path(self.markdown_qr_dir) / "markdown_qr"
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def get_markdown_file(self, md_filename) -> MarkdownFile:
        if not md_filename.endswith(".md"):
            md_filename = f"{md_filename}.md"

        if md_filename in self.md_files:
            md_filepath = self.filesystem / md_filename
            return MarkdownFile(filepath=md_filepath)

    def get_list(self, list_name:str):
        for md_file in self.md_files:
            md = self.get_markdown_file(md_file)
            if md and md.contains_list(list_name):
                return md
        return

    def update_list(self, md_file:MarkdownFile):
        """ This function updates a list given a MarkdownFile object that is full """

        if not md_file.full:
            raise ValueError(f"The MarkdownFile '{md_file.name}' does not have the required info attached to it! {md_file}")

        temp_filepath = self.filesystem / "temp.ami"

        with (temp_filepath).open("w", encoding="utf-8") as temp_file:
            with md_file.filepath.open("r", encoding="utf-8") as file:

                in_list_check = False
                for i, line in enumerate(file):

                    if in_list_check:

                        if line.startswith("- "):
                            continue
                        else:
                            in_list_check = False

                    else:
                        print(line, file=temp_file, end="")

                    if i == md_file.header_lineno:
                        in_list_check = True

                        for item in md_file.list_contents:
                            print(f"- {item}", file=temp_file, end="\n")

        os.replace(temp_filepath, md_file.filepath)


    def add_to_list(self, list_name:str, item:str, index:int=-1):
        md = self.get_list(list_name)
        if md is None:
            return

        if md:
            if index > len(md.list_contents):
                index = -1

            if index < 0:
                md.list_contents.append(item.capitalize())
            else:
                md.list_contents.insert(index, item.capitalize())

        return md

    def remove_from_list(self, list_name:str, item:str):
        md = self.get_list(list_name)
        if md is None:
            return

        if md:
            try:
                md.list_contents.remove(item.capitalize())
                return md
            except:
                return

class MarkdownFileDataModel(BaseModel):
    name: str
    html: str

    @classmethod
    def from_path(cls, markdown_filepath):
        html = get_markdown_file(markdown_filepath)
        return cls(name=markdown_filepath, html=html)
