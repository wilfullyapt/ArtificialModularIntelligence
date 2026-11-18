"""Headspace package — lazy GUI/Blueprint imports keep tool/hub tests PyQt-free."""

from __future__ import annotations

from typing import Any

from .base import Primitive
from .headspace_instructions import HeadspaceInstruction, InstructionType
from .headspace import Headspace, ami_tool, generate_qr_image, collect_tool_methods
from .hub import DelegationHub
from .settings import BaseWidgetSettings

__all__ = [
    "Primitive",
    "HeadspaceInstruction",
    "InstructionType",
    "Headspace",
    "ami_tool",
    "generate_qr_image",
    "collect_tool_methods",
    "DelegationHub",
    "BaseWidget",
    "BaseWidgetSettings",
    "Blueprint",
    "HeaderButton",
    "route",
    "plugin_template",
]


def __getattr__(name: str) -> Any:
    if name == "BaseWidget":
        from .widget import BaseWidget as _BaseWidget

        return _BaseWidget
    if name in ("Blueprint", "HeaderButton", "route", "plugin_template"):
        from . import blueprint as _blueprint

        return getattr(_blueprint, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
