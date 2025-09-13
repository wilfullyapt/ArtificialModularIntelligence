""" __init__.py """

from .base import Primitive
from .headspace_instructions import HeadspaceInstruction, InstructionType
from .settings import BaseWidgetSettings 
from .blueprint import Blueprint, HeaderButton, route, plugin_template

# Optional GUI imports - only load if needed
def _import_gui_components():
    """Lazy import GUI components to avoid PyQt6 dependencies in headless environments"""
    try:
        from .widget import BaseWidget
        from .headspace import Headspace, ami_tool, generate_qr_image
        return BaseWidget, Headspace, ami_tool, generate_qr_image
    except ImportError as e:
        # GUI dependencies not available
        return None, None, None, None

# Try to import GUI components, but don't fail if they're not available
BaseWidget, Headspace, ami_tool, generate_qr_image = _import_gui_components()

__all__ = [
    "Primitive",
    "HeadspaceInstruction",
    "InstructionType",
    "BaseWidgetSettings",
    "Blueprint",
    "HeaderButton",
    "route",
    "plugin_template",
]

# Add GUI components to __all__ if they were successfully imported
if BaseWidget is not None:
    __all__.extend(["BaseWidget", "Headspace", "ami_tool", "generate_qr_image"])
