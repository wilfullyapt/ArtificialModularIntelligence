"""
__init__.py

This file should not change
Import predefined file for the Headspace

"""

from .gui import Time as GUI
from .headspace import DatetimeHeadspace as Headspace


EXAMPLES = [
    "Set a timer for 5 minutes",
    "What's today's date?",
    "Set a reminder for this thursday to <do something>",
    "Set a reoccurring timer to replace the AC filter. Every three months starting tomorrow.",
]

__version__ = "0.1.0"

__all__ = [
    "GUI",
    "Headspace",
    "EXAMPLES",
]
