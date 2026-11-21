"""Phase B: plugin contract, install, release rollback."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ami.lifecycle.plugin_contract import validate_plugin_dir
from ami.lifecycle.plugin_install import install_plugin, parse_install_spec
from ami.lifecycle.release import ReleaseStore


def _git(cwd: Path, *args: str) -> None:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout


def _init_plugin_repo(root: Path, *, plugin_id: str = "demo_hs") -> Path:
    root.mkdir(parents=True)
    (root / "plugin.toml").write_text(
        f'id = "{plugin_id}"\nversion = "1.0.0"\nexports = ["headspace"]\n',
        encoding="utf-8",
    )
    (root / "__init__.py").write_text(
        f'''
__version__ = "1.0.0"
EXAMPLES = ["hello from {plugin_id}"]

class Headspace:
    name = "{plugin_id}"
''',
        encoding="utf-8",
    )
    _git(root, "init")
    _git(root, "config", "user.email", "test@ami")
    _git(root, "config", "user.name", "test")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    _git(root, "tag", "v1.0.0")
    return root


def test_parse_install_spec_short_and_tag():
    url, tag = parse_install_spec("acme/cool-hs@v2.0.0")
    assert url.endswith("acme/cool-hs.git")
    assert tag == "v2.0.0"


def test_validate_plugin_dir_ok(tmp_path: Path):
    repo = _init_plugin_repo(tmp_path / "src")
    c = validate_plugin_dir(repo)
    assert c.ok, c.errors
    assert c.id == "demo_hs"
    assert c.version == "1.0.0"


def test_validate_plugin_dir_missing_headspace(tmp_path: Path):
    d = tmp_path / "bad"
    d.mkdir()
    (d / "__init__.py").write_text("EXAMPLES = []\n", encoding="utf-8")
    (d / "plugin.toml").write_text(
        'id = "bad"\nversion = "0.1"\nexports = ["headspace"]\n',
        encoding="utf-8",
    )
    c = validate_plugin_dir(d)
    assert not c.ok
    assert any("Headspace" in e for e in c.errors)


def test_install_plugin_from_local_git(tmp_path: Path):
    src = _init_plugin_repo(tmp_path / "remote", plugin_id="localplug")
    plugins = tmp_path / "plugins"
    result = install_plugin(f"{src}@v1.0.0", plugins_dir=plugins)
    assert result.ok, result.message
    assert (plugins / "localplug").is_dir()
    assert (plugins / "localplug" / "plugin.toml").is_file()
    assert (plugins / "localplug" / ".git").exists() or (plugins / "localplug" / ".ami-plugin-version").is_file()


def test_release_install_activate_rollback(tmp_path: Path):
    src = tmp_path / "ami-src"
    src.mkdir()
    (src / "ami").mkdir()
    (src / "ami" / "__init__.py").write_text("# ami\n", encoding="utf-8")
    (src / "ami" / "core").mkdir()
    (src / "ami" / "core" / "__init__.py").write_text("", encoding="utf-8")
    (src / "ami" / "core" / "interaction.py").write_text("X=1\n", encoding="utf-8")
    (src / "ami" / "headspace").mkdir()
    (src / "ami" / "headspace" / "__init__.py").write_text("", encoding="utf-8")
    (src / "ami" / "headspace" / "hub.py").write_text("Y=1\n", encoding="utf-8")
    _git(src, "init")
    _git(src, "config", "user.email", "t@ami")
    _git(src, "config", "user.name", "t")
    _git(src, "add", "-A")
    _git(src, "commit", "-m", "a")
    _git(src, "tag", "v0.1.0")
    (src / "ami" / "__init__.py").write_text("# ami v2\n", encoding="utf-8")
    _git(src, "add", "-A")
    _git(src, "commit", "-m", "b")
    _git(src, "tag", "v0.2.0")

    store = ReleaseStore(tmp_path / "releases", source_repo=src)
    r1 = store.install_tag("v0.1.0", run_smoke=True)
    assert r1.ok, r1.message
    r2 = store.install_tag("v0.2.0", run_smoke=True)
    assert r2.ok, r2.message

    a1 = store.activate("v0.1.0")
    assert a1.ok, a1.message
    assert store.current_tag() == "v0.1.0"

    a2 = store.activate("v0.2.0")
    assert a2.ok, a2.message
    assert store.current_tag() == "v0.2.0"
    assert store.previous_tag() == "v0.1.0"

    rb = store.rollback()
    assert rb.ok, rb.message
    assert store.current_tag() == "v0.1.0"
