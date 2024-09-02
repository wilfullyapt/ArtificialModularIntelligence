"""
__init__.py
"""

import pytz

from .headspace import Headspace, Dialog
from .ai import AI

def timezones():
    """ Get all pytz timezones """
    return pytz.all_timezones
