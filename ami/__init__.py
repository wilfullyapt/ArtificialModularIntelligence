"""Artificial Modular Intelligence package root.

Heavy subsystems (core, AI, headspace) import lazily so builtin plugins and unit
tests can load without PortAudio / full voice stack installed.
"""

__version__ = "0.1.0"


def timezones():
    """Get all pytz timezones."""
    import pytz

    return pytz.all_timezones


def __getattr__(name: str):
    if name == "core":
        from . import core as _core

        return _core
    if name == "AI":
        from .ai import AI as _AI

        return _AI
    if name == "Headspace":
        from .headspace import Headspace as _Headspace

        return _Headspace
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "core",
    "AI",
    "Headspace",
    "timezones",
    "__version__",
]
