""" __init__.py """

import pytz

from . import core

def timezones():
    """ Get all pytz timezones """
    return pytz.all_timezones

# Lazy imports for heavy dependencies to avoid loading GUI/audio deps in headless environments
def __getattr__(name):
    """Lazy import heavy modules on demand"""
    if name == "Headspace":
        from .headspace import Headspace
        return Headspace
    elif name == "AI":
        from .ai import AI
        return AI
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__version__ = "0.1.0"

__all__ = [
    "core",
    "AI",
    "Headspace",
    "timezones"
]
