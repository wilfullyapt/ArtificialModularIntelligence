"""ami.flask package | All core Flask related contained"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import FlaskManager

__all__ = ["FlaskManager", "resolve_gunicorn_options"]


def __getattr__(name: str):
    if name == "FlaskManager":
        from .manager import FlaskManager as _FM

        return _FM
    if name == "resolve_gunicorn_options":
        from .gunicorn_opts import resolve_gunicorn_options as _r

        return _r
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
