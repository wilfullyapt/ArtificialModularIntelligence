"""
__init__.py for AMI Neighbors Headspace Plugin

Runtimes: GUI, Headspace, Blueprint (lazy-imported so domain tests need no PyQt6).
EXAMPLES route natural-language prompts into this headspace.
"""

from __future__ import annotations

from typing import Any

EXAMPLES = [
    "Who are my neighbors?",
    "List local AMI devices on the mesh",
    "List internet neighbors",
    "Announce my presence on the mesh",
    "What's my mesh status?",
    "Tell me about neighbor Kitchen",
    "Set my neighbor display name to Living Room",
]

__version__ = "0.1.0"


def __getattr__(name: str) -> Any:
    if name == "GUI":
        from .gui import NeighborsGUI as GUI

        return GUI
    if name == "Headspace":
        from .headspace import NeighborsHeadspace as Headspace

        return Headspace
    if name == "Blueprint":
        from .blueprint import NeighborsBlueprint as Blueprint

        return Blueprint
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "GUI",
    "Headspace",
    "Blueprint",
    "EXAMPLES",
]
