"""
__init__.py for Media Headspace Plugin

Note: this builtin is still thin / legacy-shaped (tk GUI class names).
Enabled only when listed in enabled_headspaces.
"""

from .gui import Markdown as GUI
from .headspace import Media as Headspace
from .blueprint import Markdown as Blueprint

EXAMPLES = [
    "Play some music",
    "List videos from a YouTube creator",
    "What media can you play",
]

__version__ = "0.1.0"

__all__ = [
    "GUI",
    "Headspace",
    "Blueprint",
    "EXAMPLES",
]
