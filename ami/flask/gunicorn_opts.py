"""Gunicorn option resolution (no gunicorn import — headless-safe)."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class _ConfigLike(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...


def resolve_gunicorn_options(config: _ConfigLike | None = None) -> dict:
    """
    Kiosk-friendly defaults: 1 worker, few threads.

    Config under top-level `server:`:
      workers (default 1)
      threads (default 2)
      kill_ami_on_exit (default false)
    """
    if config is None:
        from ami.core.config import Config

        config = Config()
    server = config.get("server", {}) or {}
    if not isinstance(server, Mapping):
        server = {}
    try:
        workers = max(1, int(server.get("workers", 1)))
    except (TypeError, ValueError):
        workers = 1
    try:
        threads = max(1, int(server.get("threads", 2)))
    except (TypeError, ValueError):
        threads = 2
    return {
        "workers": workers,
        "threads": threads,
        "kill_ami_on_exit": bool(server.get("kill_ami_on_exit", False)),
    }
