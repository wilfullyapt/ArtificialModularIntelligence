"""
__init__.py
"""

import pytz

from ami.headspace import Headspace, Dialog
from ami.ai import AI

def timezones():
    """ Get all pytz timezones """
    return pytz.all_timezones
