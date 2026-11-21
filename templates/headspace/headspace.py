"""Minimal Headspace — domain tools only (no GUI required)."""

from __future__ import annotations

from ami.headspace import Headspace, ami_tool


class DemoHeadspace(Headspace):
    """Starter headspace for third-party plugins."""

    @ami_tool
    def ping(self) -> str:
        """Return a simple alive string for routing smoke tests."""
        return "demo_headspace: pong"

    @ami_tool
    def echo(self, message: str) -> str:
        """Echo a short message back to the agent."""
        text = (message or "").strip()
        if not text:
            return "echo: (empty message)"
        if len(text) > 280:
            text = text[:277] + "..."
        return f"echo: {text}"
