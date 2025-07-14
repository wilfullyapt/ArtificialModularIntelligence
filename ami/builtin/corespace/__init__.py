"""
__init__.py for a AMI Headspace Plugin

The standard convention is to define the import to one of the three runtimes,
[ 'GUI', 'Headspace', 'Blueprint' ]

Secondarily there shoule be a List of examples prompts so AI understands the context to route to this Headspace
"""

from .gui import CorespaceGUI as GUI
from .headspace import CorespaceHeadspace as Headspace


EXAMPLES = [
    "Set a timer for 5 minutes",
    "What's today's date?",
    "Set a reminder for this thursday to <do something>",
    "Set a reoccurring reminder to <do something>. Every three months starting tomorrow.",
    "Can you tell me about ...",
    "Can you explain to me ...",

]

__version__ = "0.1.0"

__all__ = [
    "GUI",
    "Headspace",
    "EXAMPLES",
]
