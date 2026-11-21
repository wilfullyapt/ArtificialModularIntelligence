"""Unit tests for ami.cli plugin enable/disable against real enabled_headspaces list."""

from __future__ import annotations

from pathlib import Path

import yaml

from ami.cli import cmd_plugin_disable, cmd_plugin_enable, cmd_plugin_list, _load_raw_config


def test_plugin_enable_disable_roundtrip(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "ami_config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "enabled_headspaces": ["corespace"],
                "timezone": "UTC",
            }
        ),
        encoding="utf-8",
    )

    assert cmd_plugin_enable("markdown", config_path=cfg) == 0
    data = _load_raw_config(cfg)
    assert data["enabled_headspaces"] == ["corespace", "markdown"]

    assert cmd_plugin_enable("markdown", config_path=cfg) == 0  # idempotent
    data = _load_raw_config(cfg)
    assert data["enabled_headspaces"] == ["corespace", "markdown"]

    assert cmd_plugin_disable("corespace", config_path=cfg) == 0
    data = _load_raw_config(cfg)
    assert data["enabled_headspaces"] == ["markdown"]


def test_refuse_enable_old_attic(tmp_path: Path):
    cfg = tmp_path / "ami_config.yaml"
    cfg.write_text("enabled_headspaces: []\n", encoding="utf-8")
    assert cmd_plugin_enable("old", config_path=cfg) == 2
    assert _load_raw_config(cfg).get("enabled_headspaces") == []


def test_plugin_list_runs(tmp_path: Path, monkeypatch, capsys):
    # list uses Config singleton paths; just ensure it returns 0 with a temp config copy
    cfg = tmp_path / "ami_config.yaml"
    cfg.write_text("enabled_headspaces:\n  - corespace\n", encoding="utf-8")
    code = cmd_plugin_list(config_path=cfg)
    assert code == 0
    out = capsys.readouterr().out
    assert "config:" in out
