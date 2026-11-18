"""
__init__.py for a AMI Headspace Plugin

Runtimes: GUI, Headspace
EXAMPLES route natural-language prompts into this headspace.
"""

from .gui import CompanyAGIGUI as GUI
from .headspace import CompanyHeadspace as Headspace

EXAMPLES = [
    "Analyze my company goals",
    "Update my goals",
    "What should I focus on this week for the company",
    "Add a goal to ship Neighbors mesh",
]

__version__ = "0.1.0"

__all__ = [
    "GUI",
    "Headspace",
    "EXAMPLES",
]
