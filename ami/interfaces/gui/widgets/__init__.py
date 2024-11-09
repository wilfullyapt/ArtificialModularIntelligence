from ami.interfaces.gui.widgets.base import BuildtinWidget, HeadspaceWidget
from ami.interfaces.gui.widgets.builtins import ClockWidget, NotificationStack

builtin_widgets = {
    'clock': ClockWidget,
    'notifications': NotificationStack
}

__all__ = [ 'BuildtinWidget', 'HeadspaceWidget' ]
