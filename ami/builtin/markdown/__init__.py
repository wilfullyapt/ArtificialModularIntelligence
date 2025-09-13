"""
__init__.py for a AMI Headspace Plugin

The standard convention is to define the import to one of the three runtimes,
[ 'GUI', 'Headspace', 'Blueprint' ]

Secondarily there shoule be a List of examples prompts so AI understands the context to route to this Headspace
"""

# Lazy import for GUI to avoid PyQt6 dependencies in headless environments
def __getattr__(name):
    """Lazy import GUI components on demand"""
    if name == "GUI":
        from .gui import MarkdownGUI as GUI
        return GUI
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
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
    "GUI",
    "Headspace",
    "Blueprint",
    "EXAMPLES",
]
