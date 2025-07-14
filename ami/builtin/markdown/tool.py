from pathlib import Path
from typing import Any, List, Tuple

import markdown
import tempfile
import shutil
from pathlib import Path
from typing import Any, List, Tuple, Dict
from threading import Lock

from pydantic import BaseModel

from ami.core import LogBase

def convert_md_to_html(md_file):
    with open(md_file, 'r') as f:
        md_content = f.read()
        html_content = markdown.markdown(md_content)
        return html_content

def extract_list_info(file_path: Path, listname: str) -> Tuple[int, List[str]]:
    """
    Extracts the header line number and the list items under the specified header from a markdown file.

    Args:
        file_path: Path to the markdown file.
        listname: The header name of the list to extract.

    Returns:
        A tuple containing the header line number and the list items if found, otherwise None.
    """
    try:
        with file_path.open('r',  encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path.name}' was not found.")

    for i, line in enumerate(lines, start=0):
        if line.startswith("#") and line.lstrip("#")[0] == " ":
            if listname == line.lstrip("#").strip():
                header_line = i
                list_items = []

                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line.startswith("-"):
                        while j < len(lines) and lines[j].strip().startswith("-"):
                            item = lines[j].strip().lstrip("-").strip()
                            list_items.append(item)
                            j += 1
                        return (header_line, list_items)
                    elif next_line.startswith("#"):
                        break

    raise ValueError(f"The {file_path.name} markdown file doesn't contain a {listname} list")

class MarkdownList(BaseModel):
    markdown_file: Any
    listname: str
    contents: List[str]
    lineno: int

    def __contains__(self, value: str) -> bool:
        return value in self.contents

    def __len__(self) -> int:
        return len(self.contents)

class MarkdownFile:

    def __init__(self, markdown_filepath: Path):
        self._filepath = markdown_filepath

    def __contains__(self, value: str):
        return value in self.lists

    @property
    def filepath(self) -> Path:
        return self._filepath

    @property
    def exists(self):
        return self.filepath.is_file()

    @property
    def name(self) -> str:
        return self._filepath.name

    @property
    def lists(self) -> List[str]:
        """ Returns a list of all headers that are in place as list names """
        if not self.exists:
            raise FileNotFoundError(f"The file '{self.filepath.name}' does not exist.")

        with self.filepath.open("r", encoding="utf-8") as file:
            lists = []
            for _, line in enumerate(file):
                if line.startswith("#") and line.lstrip("#")[0] == " ":
                    lists.append(line.lstrip("#").strip())

        return lists

    def get_list(self, listname: str) -> MarkdownList:
        """ Returns a list object for the Markdown file """
        if listname in self.lists:
            lineno, list_items = extract_list_info(self.filepath, listname)
            return MarkdownList(
                markdown_file=self,
                listname=listname,
                contents=list_items,
                lineno=lineno
            )
        raise ValueError(f"'{listname}' list cannot be found in {self.filepath.name}")

class Markdown(LogBase):

    def __init__(self, base_path: Path, markdown_files: List[str]):
        self._filesystem: Path = base_path
        self._md_files: List[str] = markdown_files
        self._file_cache: Dict[str, List[str]] = {}
        self._cache_lock = Lock()
        self.logs.debug(f"Markdown Files for MarkdownTool: {self._md_files}")
    
    def _get_file_lines(self, filepath: Path) -> List[str]:
        """Get file lines with caching"""
        with self._cache_lock:
            cache_key = str(filepath)
            if cache_key not in self._file_cache:
                try:
                    with filepath.open('r', encoding='utf-8') as f:
                        self._file_cache[cache_key] = f.readlines()
                except FileNotFoundError:
                    return []
            return self._file_cache[cache_key].copy()
    
    def _write_file_atomic(self, filepath: Path, lines: List[str]):
        """Write file atomically and update cache"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                       dir=filepath.parent, delete=False) as tmp:
            tmp.writelines(lines)
            tmp_path = Path(tmp.name)
        
        shutil.move(str(tmp_path), str(filepath))
        
        with self._cache_lock:
            self._file_cache[str(filepath)] = lines.copy()
    
    def _invalidate_cache(self, filepath: Path):
        """Remove file from cache"""
        with self._cache_lock:
            self._file_cache.pop(str(filepath), None)

    @property
    def filesystem(self) -> Path:
        return self._filesystem

    @property
    def md_files(self):
        return self._md_files

    @property
    def lists(self):
        md_lists = []
        for md in [ MarkdownFile(self.filesystem/md_file) for md_file in self.md_files ]:
            md_lists.extend(md.lists)
        return md_lists


    @property
    def markdowns(self) -> List[MarkdownFile]:
        return [ MarkdownFile(self.filesystem / md_file) for md_file in self.md_files ]

    def get_markdown_file(self, md_filename) -> MarkdownFile:
        self.logs.debug(f"get_markdown_file called for {md_filename}")
        if not md_filename.endswith(".md"):
            md_filename = f"{md_filename}.md"

        if md_filename in self.md_files:
            return MarkdownFile(self.filesystem / md_filename)

        raise ValueError(f"'{md_filename}' doesn't exist!")

    def get_list(self, list_name:str) -> MarkdownList:
        for md in self.markdowns:
            if list_name in md:
                return md.get_list(list_name)
        raise ValueError(f"The '{list_name}' list cannot be found!")

    def add_to_list(self, list_name: str, item: str, index: int = -1):
        """Adds an item to the specified list in a Markdown file at the given index."""
        md_list = self.get_list(list_name)
        
        # Add item to contents (don't force lowercase)
        if index == -1:
            md_list.contents.append(item)
        else:
            md_list.contents.insert(index, item)
        
        lines = self._get_file_lines(md_list.markdown_file.filepath)
        
        # Find list boundaries more reliably
        list_start = md_list.lineno + 1
        while list_start < len(lines):
            line = lines[list_start].strip()
            if line.startswith('-') or line.startswith('*'):
                break
            elif line and not line.startswith('#'):
                list_start += 1
            else:
                break
        
        list_end = list_start
        while list_end < len(lines):
            line = lines[list_end].strip()
            if line.startswith('-') or line.startswith('*'):
                list_end += 1
            elif not line:  # Empty line continues list
                list_end += 1
            else:
                break
        
        # Reconstruct list with proper formatting
        new_list_lines = [f"- {content}\n" for content in md_list.contents]
        new_lines = lines[:list_start] + new_list_lines + lines[list_end:]
        
        self._write_file_atomic(md_list.markdown_file.filepath, new_lines)

    def remove_from_list(self, list_name: str, item: str):
        """Removes a specified item from the list in a Markdown file."""
        md_list = self.get_list(list_name)
        
        # Case-insensitive search for item
        item_to_remove = None
        for content in md_list.contents:
            if content.lower() == item.lower():
                item_to_remove = content
                break
        
        if item_to_remove is None:
            raise ValueError(f"Item '{item}' not found in list '{list_name}'")
        
        md_list.contents.remove(item_to_remove)
        
        lines = self._get_file_lines(md_list.markdown_file.filepath)
        
        # Find list boundaries (same logic as add_to_list)
        list_start = md_list.lineno + 1
        while list_start < len(lines):
            line = lines[list_start].strip()
            if line.startswith('-') or line.startswith('*'):
                break
            elif line and not line.startswith('#'):
                list_start += 1
            else:
                break
        
        list_end = list_start
        while list_end < len(lines):
            line = lines[list_end].strip()
            if line.startswith('-') or line.startswith('*'):
                list_end += 1
            elif not line:
                list_end += 1
            else:
                break
        
        # Reconstruct list
        new_list_lines = [f"- {content}\n" for content in md_list.contents]
        new_lines = lines[:list_start] + new_list_lines + lines[list_end:]
        
        self._write_file_atomic(md_list.markdown_file.filepath, new_lines)
