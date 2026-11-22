"""Render systemd user unit for AMI kiosk appliance."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def default_unit_path(home: Optional[Path] = None) -> Path:
    h = Path(home) if home is not None else Path.home()
    return h / ".config" / "systemd" / "user" / "ami.service"


def render_user_unit(
    *,
    exec_start: str,
    working_directory: str,
    description: str = "AMI home kiosk appliance",
    display: str = ":0",
) -> str:
    """
    User-level unit. Requires a graphical session for PyQt glass.

    exec_start: full command, e.g. /home/pi/ArtificialModularIntelligence/.venv/bin/python -m ami.cli run
    """
    return f"""# AMI kiosk — managed by `python -m ami.cli systemd install`
[Unit]
Description={description}
After=network-online.target graphical-session.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={working_directory}
ExecStart={exec_start}
Restart=on-failure
RestartSec=5
Environment=DISPLAY={display}
Environment=PYTHONUNBUFFERED=1
# Wayland/XDG when present
Environment=XDG_SESSION_TYPE=x11

[Install]
WantedBy=default.target
"""


def write_user_unit(
    *,
    unit_path: Path,
    exec_start: str,
    working_directory: str,
    display: str = ":0",
) -> Path:
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    text = render_user_unit(
        exec_start=exec_start,
        working_directory=working_directory,
        display=display,
    )
    unit_path.write_text(text, encoding="utf-8")
    return unit_path
