""" __init__.py """

import pytz

from . import core
from .headspace import Headspace
from .ai import AI

def timezones():
    """ Get all pytz timezones """
    return pytz.all_timezones

__version__ = "0.1.0"

__all__ = [
    "core",
    "AI",
    "Headspace",
    "timezones"
]
