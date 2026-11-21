"""Phase D: receipts index + slim gunicorn options."""

from __future__ import annotations

import json
from pathlib import Path

from ami.core.receipts import list_receipts, load_receipt
from ami.flask.gunicorn_opts import resolve_gunicorn_options


class _FakeCfg:
    def __init__(self, server=None):
        self._server = server or {}

    def get(self, key, default=None):
        if key == "server":
            return self._server
        return default


def test_resolve_gunicorn_defaults():
    opts = resolve_gunicorn_options(_FakeCfg())
    assert opts["workers"] == 1
    assert opts["threads"] == 2
    assert opts["kill_ami_on_exit"] is False


def test_resolve_gunicorn_custom():
    opts = resolve_gunicorn_options(
        _FakeCfg({"workers": 4, "threads": 8, "kill_ami_on_exit": True})
    )
    assert opts["workers"] == 4
    assert opts["threads"] == 8
    assert opts["kill_ami_on_exit"] is True


def test_list_and_load_receipts(tmp_path: Path):
    sess = tmp_path / "sess1" / "turns"
    sess.mkdir(parents=True)
    payload = {
        "session_id": "sess1",
        "turn_id": "turn-abc",
        "human_text": "hello",
        "final_text": "world",
        "route_summary": "corespace",
        "started_at": "2026-01-02T00:00:00",
        "finished_at": "2026-01-02T00:00:01",
        "spans": [],
    }
    (sess / "turn-abc.json").write_text(json.dumps(payload), encoding="utf-8")
    items = list_receipts(tmp_path, limit=10)
    assert len(items) == 1
    assert items[0].human_text == "hello"
    loaded = load_receipt(tmp_path, "sess1", "turn-abc")
    assert loaded is not None
    assert loaded["final_text"] == "world"
    assert load_receipt(tmp_path, "sess1", "missing") is None


def test_cmd_run_release_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    from ami.core.config import Config

    Config._instance = None
    Config._file_observer = None
    Config._count = 0

    from ami.cli import cmd_run

    code = cmd_run(use_release=True)
    assert code == 1
