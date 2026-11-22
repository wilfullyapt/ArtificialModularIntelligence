"""Day-zero kiosk bootstrap: config, secrets scaffold, systemd unit text."""

from .bootstrap import (
    ENV_TEMPLATE,
    bootstrap,
    ensure_ami_home,
    ensure_config,
    ensure_env_scaffold,
    secrets_status,
)
from .systemd_unit import render_user_unit, default_unit_path

__all__ = [
    "ENV_TEMPLATE",
    "bootstrap",
    "ensure_ami_home",
    "ensure_config",
    "ensure_env_scaffold",
    "secrets_status",
    "render_user_unit",
    "default_unit_path",
]
