"""
__init__.py for a AMI Headspace Plugin

The standard convention is to define the import to one of the three runtimes,
[ 'GUI', 'Headspace', 'Blueprint' ]

Secondarily there shoule be a List of examples prompts so AI understands the context to route to this Headspace
"""

from .gui import DateTime as GUI
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
