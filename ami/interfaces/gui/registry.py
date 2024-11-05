""" Specific Widget Registration """

from .clock import ClockWidget
from .notifications import NotificationStack

builtin_widgets = {
    'clock': ClockWidget,
    'notifications': NotificationStack
}
