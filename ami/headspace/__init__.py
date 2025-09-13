"""
The Headspaces sub library controls how a plugin integrates and interacts with the system.
Primitive           -> Implemented at all levels for standard naming and calling conventions. BP, HS, GUI.

Headspace           -> Headspace Agent specific implementation for subclassing
InscructionType     -> HS Instruction formating when completing a delerverable tool
ami_tool            -> HS tool decorator
generate_qr_image   -> HS tool for creating QR links

BaseWidget          -> BaseWidget for subclassing a widget for a Headspace
BaseWidgetSettings  -> Base widget settings for Headspace widgets

Blueprint           -> AMI specific Flask Blueprint for Headspace subclassing
HeaderButton        -> Buttom speicifcs for integrating into the Base Flask Server
route               -> AMI specific route decorator to define a route
plugin_template     -> AMI specific Flask templating return
"""

from .base import Primitive
from .headspace_instructions import HeadspaceInstruction, InstructionType
from .headspace import Headspace, ami_tool, generate_qr_image
from .widget import BaseWidget
from .settings import BaseWidgetSettings 
from .blueprint import Blueprint, HeaderButton, route, plugin_template

__all__ = [
    "Primitive",
    "HeadspaceInstruction",
    "InstructionType",
    "Headspace",
    "ami_tool",
    "generate_qr_image",
    "BaseWidget",
    "BaseWidgetSettings",
    "Blueprint",
    "HeaderButton",
    "route",
    "plugin_template",
]
