""" This file controls the builtin widgets for the gui """

from .base import BuildtinWidget, HeadspaceWidget
from .builtins import ClockWidget, NotificationStack

builtin_widgets = {
    'clock': ClockWidget,
    'notifications': NotificationStack
}

__all__ = [ 'BuildtinWidget', 'HeadspaceWidget' ]
