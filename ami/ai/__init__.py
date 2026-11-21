"""AI subsystem package — lazy exports so STT/helpers import without PyQt stack."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AI",
    "Brain",
    "AIState",
    "AIStateMachine",
]


def __getattr__(name: str) -> Any:
    if name == "AI":
        from .ai import AI as _AI

        return _AI
    if name == "Brain":
        from .brain import Brain as _Brain

        return _Brain
    if name in ("AIState", "AIStateMachine"):
        from . import state as _state

        return getattr(_state, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
