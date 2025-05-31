"""
__init__.py for a AMI Headspace Plugin

The standard convention is to define the import to one of the three runtimes,
[ 'GUI', 'Headspace', 'Blueprint' ]

Secondarily there shoule be a List of examples prompts so AI understands the context to route to this Headspace
"""

from .gui import MarkdownGUI as GUI
from .headspace import Markdown as Headspace
from .blueprint import Markdown as Blueprint

EXAMPLES = [
    "Let me edit a markdown file",
    "Add an item to my list",
    "Remove an item from my list",
    "I need to download a list",
    "I need the qr code for a list"
]

__version__ = "0.1.0"

__all__ = [
    'GUI',
    'Headspace',
    'Blueprint'
]
