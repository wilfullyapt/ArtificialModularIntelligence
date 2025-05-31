"""
__init__.py

This file should not change
Import predefined file for the Headspace

"""

from .blueprint import Markdown as MarkdownBlueprint
from .gui import Markdown as MarkdownGui
from .headspace import Markdown as MarkdownHeadspace

# Optional prompts
try:
    from .prompts import AGENT, ROUTING
except ImportError:
    MarkdownPrompts = None

def get_blueprint():
    return MarkdownBlueprint

def get_gui():
    return MarkdownGui

def get_headspace():
    return MarkdownHeadspace

def get_prompts():
    return MarkdownPrompts if MarkdownPrompts is not None else None
