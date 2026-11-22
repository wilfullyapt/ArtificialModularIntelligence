"""P0 day-zero: init, secrets presence, systemd unit render."""

from __future__ import annotations

from pathlib import Path

from ami.cli import cmd_init, cmd_secrets_check, cmd_systemd_install, cmd_systemd_status
from ami.day0.bootstrap import (
    ENV_TEMPLATE,
    bootstrap,
    ensure_ami_home,
    ensure_config,
    ensure_env_scaffold,
    parse_env_keys,
    secrets_status,
)
from ami.day0.systemd_unit import render_user_unit


def test_ensure_ami_home_creates_subdirs(tmp_path: Path):
    home = ensure_ami_home(tmp_path / ".ami")
    assert home.is_dir()
    for name in ("data", "plugins", "releases", "conversations", "logs"):
        assert (home / name).is_dir()


def test_config_created_once(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    template = root / "config_template.yaml"
    home = tmp_path / ".ami"
    home.mkdir()
    path, created = ensure_config(ami_home=home, template_path=template)
    assert created is True
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "enabled_headspaces" in text
    # second call does not overwrite user edit
    path.write_text("enabled_headspaces: [corespace]\n# user\n", encoding="utf-8")
    path2, created2 = ensure_config(ami_home=home, template_path=template)
    assert created2 is False
    assert "user" in path2.read_text(encoding="utf-8")


def test_env_scaffold_no_overwrite(tmp_path: Path):
    home = tmp_path / ".ami"
    home.mkdir()
    p, created = ensure_env_scaffold(ami_home=home)
    assert created is True
    assert "XAI_API_KEY" in p.read_text(encoding="utf-8")
    p.write_text("XAI_API_KEY=super-secret\n", encoding="utf-8")
    p2, created2 = ensure_env_scaffold(ami_home=home)
    assert created2 is False
    assert "super-secret" in p2.read_text(encoding="utf-8")


def test_parse_env_and_secrets_status_never_returns_values(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("XAI_API_KEY=shh\n# ANTHROPIC_API_KEY=\nOPENAI_API_KEY=\n", encoding="utf-8")
    parsed = parse_env_keys(env.read_text(encoding="utf-8"))
    assert parsed["XAI_API_KEY"] is True
    assert parsed.get("OPENAI_API_KEY") is False
    st = secrets_status(env)
    assert "shh" not in str(st)
    assert "XAI_API_KEY" in st["keys_set"]
    assert "ANTHROPIC_API_KEY" in st["keys_missing_known"]


def test_bootstrap_and_cli_init(tmp_path: Path, capsys):
    root = Path(__file__).resolve().parents[2]
    template = root / "config_template.yaml"
    home = tmp_path / "amihome"
    result = bootstrap(ami_home=home, template_path=template)
    assert result.config_created and result.env_created
    assert cmd_init(ami_home=home) == 0  # idempotent
    out = capsys.readouterr().out
    assert "config ok" in out or "created config" in out
    assert cmd_secrets_check(ami_home=home) == 0


def test_secrets_check_missing_file(tmp_path: Path):
    assert cmd_secrets_check(ami_home=tmp_path / "empty") == 1


def test_systemd_unit_render_and_install(tmp_path: Path, capsys):
    text = render_user_unit(
        exec_start="/opt/ami/.venv/bin/python -m ami.cli run",
        working_directory="/opt/ami",
        display=":0",
    )
    assert "ExecStart=/opt/ami/.venv/bin/python -m ami.cli run" in text
    assert "WorkingDirectory=/opt/ami" in text
    assert "WantedBy=default.target" in text

    unit = tmp_path / "ami.service"
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".venv" / "bin").mkdir(parents=True)
    (repo / ".venv" / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
    (repo / ".venv" / "bin" / "python").chmod(0o755)
    assert cmd_systemd_install(repo_dir=repo, unit_path=unit, display=":1") == 0
    body = unit.read_text(encoding="utf-8")
    assert str(repo) in body
    assert "ami.cli run" in body
    assert "DISPLAY=:1" in body
    assert cmd_systemd_status(unit_path=unit) == 0


def test_env_template_constant_safe():
    assert "never commit" in ENV_TEMPLATE.lower() or "Never commit" in ENV_TEMPLATE
    assert "XAI_API_KEY" in ENV_TEMPLATE
