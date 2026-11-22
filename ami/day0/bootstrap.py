"""Pure day-zero filesystem bootstrap (no GUI)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ENV_TEMPLATE = """# AMI secrets — local only. Never commit this file.
# Presence is enough for `ami secrets check`; values are never printed.

# Cloud LLM (use the backend you set in ami_config.yaml)
# XAI_API_KEY=
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=

# Optional internet neighbors directory bearer
# AMI_NEIGHBORS_TOKEN=
"""

# Keys we acknowledge for presence checks (expand carefully)
KNOWN_SECRET_KEYS = (
    "XAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "AMI_NEIGHBORS_TOKEN",
)


@dataclass
class BootstrapResult:
    ami_home: Path
    config_path: Path
    env_path: Path
    config_created: bool
    env_created: bool
    messages: List[str]


def ensure_ami_home(home: Optional[Path] = None) -> Path:
    root = Path(home) if home is not None else Path.home() / ".ami"
    root.mkdir(parents=True, exist_ok=True)
    for sub in ("data", "plugins", "releases", "conversations", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def ensure_config(
    *,
    ami_home: Path,
    template_path: Path,
    force: bool = False,
) -> Tuple[Path, bool]:
    """Copy config template if missing (or force). Never deletes existing config unless force."""
    dest = ami_home / "ami_config.yaml"
    if dest.is_file() and not force:
        return dest, False
    if not template_path.is_file():
        raise FileNotFoundError(f"config template missing: {template_path}")
    shutil.copy2(template_path, dest)
    return dest, True


def ensure_env_scaffold(*, ami_home: Path, force: bool = False) -> Tuple[Path, bool]:
    """Create ~/.ami/.env from template if missing. Never overwrite secrets unless force."""
    dest = ami_home / ".env"
    if dest.is_file() and not force:
        return dest, False
    dest.write_text(ENV_TEMPLATE, encoding="utf-8")
    try:
        dest.chmod(0o600)
    except OSError:
        pass
    return dest, True


def parse_env_keys(text: str) -> Dict[str, bool]:
    """Return map of KEY -> has_nonempty_value. Does not return values."""
    present: Dict[str, bool] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        cleaned = val.strip().strip("\"'")
        present[key] = bool(cleaned)
    return present


def secrets_status(env_path: Path) -> Dict[str, object]:
    """Presence-only report. Never includes secret values."""
    if not env_path.is_file():
        return {
            "env_path": str(env_path),
            "exists": False,
            "keys_set": [],
            "keys_missing_known": list(KNOWN_SECRET_KEYS),
        }
    text = env_path.read_text(encoding="utf-8")
    parsed = parse_env_keys(text)
    keys_set = sorted(k for k, ok in parsed.items() if ok)
    missing = [k for k in KNOWN_SECRET_KEYS if not parsed.get(k)]
    return {
        "env_path": str(env_path),
        "exists": True,
        "keys_set": keys_set,
        "keys_missing_known": missing,
    }


def bootstrap(
    *,
    ami_home: Optional[Path] = None,
    template_path: Path,
    force_config: bool = False,
    force_env: bool = False,
) -> BootstrapResult:
    home = ensure_ami_home(ami_home)
    cfg_path, cfg_new = ensure_config(ami_home=home, template_path=template_path, force=force_config)
    env_path, env_new = ensure_env_scaffold(ami_home=home, force=force_env)
    msgs: List[str] = []
    if cfg_new:
        msgs.append(f"created config: {cfg_path}")
    else:
        msgs.append(f"config ok: {cfg_path}")
    if env_new:
        msgs.append(f"created secrets scaffold: {env_path}")
    else:
        msgs.append(f"secrets file ok: {env_path}")
    return BootstrapResult(
        ami_home=home,
        config_path=cfg_path,
        env_path=env_path,
        config_created=cfg_new,
        env_created=env_new,
        messages=msgs,
    )
