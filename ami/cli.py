"""AMI operator CLI (Python-first).

Config SoR: ~/.ami/ami_config.yaml → enabled_headspaces: [list]
Releases:  ~/.ami/releases/{CURRENT,PREVIOUS,<tag>/}
Plugins:   ~/.ami/plugins/<id>/

Usage:
  python -m ami.cli doctor
  python -m ami.cli plugin list|enable|disable|install|validate
  python -m ami.cli release status|install|activate|rollback|list
  python -m ami.cli directory serve
  python -m ami.cli run
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

from ami.core.config import Config, get_config_filepath


def _load_raw_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data


def _save_raw_config(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def _enabled_list(data: Dict[str, Any]) -> List[str]:
    raw = data.get("enabled_headspaces") or []
    if not isinstance(raw, list):
        return []
    return [str(x).strip() for x in raw if str(x).strip()]


def cmd_plugin_list(*, config_path: Optional[Path] = None) -> int:
    path = config_path or get_config_filepath()
    data = _load_raw_config(path)
    enabled = set(_enabled_list(data))

    cfg = Config()
    from ami.core.registry import PluginCache

    cache = PluginCache.load_from_plugin_dir(cfg.builtin_plugins, cfg.plugins_dir)
    names = sorted(cache.names)
    if not names:
        print("(no plugins discovered)")
        print(f"config: {path}")
        return 0

    print(f"{'NAME':<16} {'VERSION':<10} {'SOURCE':<12} ENABLED")
    for name in names:
        plugin = cache[name]
        if plugin is None:
            continue
        on = "yes" if name in enabled else "no"
        src = "builtin" if plugin.repo_url == "builtin" else "plugin"
        print(f"{name:<16} {plugin.version:<10} {src:<12} {on}")
    print(f"\nconfig: {path}")
    print(f"plugins dir: {cfg.plugins_dir}")
    return 0


def cmd_plugin_enable(name: str, *, config_path: Optional[Path] = None) -> int:
    path = config_path or get_config_filepath()
    data = _load_raw_config(path)
    enabled = _enabled_list(data)
    key = name.strip()
    if not key:
        print("plugin name required", file=sys.stderr)
        return 2
    if key == "old":
        print("refusing to enable attic package 'old'", file=sys.stderr)
        return 2
    if key not in enabled:
        enabled.append(key)
        data["enabled_headspaces"] = enabled
        _save_raw_config(path, data)
        print(f"enabled: {key}")
    else:
        print(f"already enabled: {key}")
    return 0


def cmd_plugin_disable(name: str, *, config_path: Optional[Path] = None) -> int:
    path = config_path or get_config_filepath()
    data = _load_raw_config(path)
    enabled = _enabled_list(data)
    key = name.strip()
    if key not in enabled:
        print(f"not enabled: {key}")
        return 0
    data["enabled_headspaces"] = [x for x in enabled if x != key]
    _save_raw_config(path, data)
    print(f"disabled: {key}")
    return 0


def cmd_plugin_validate(path_str: str) -> int:
    from ami.lifecycle import validate_plugin_dir

    contract = validate_plugin_dir(Path(path_str))
    print(f"id: {contract.id}")
    print(f"version: {contract.version}")
    print(f"source: {contract.source}")
    print(f"exports: {contract.exports}")
    for w in contract.warnings:
        print(f"warning: {w}")
    if contract.ok:
        print("OK")
        return 0
    for e in contract.errors:
        print(f"error: {e}", file=sys.stderr)
    return 1


def cmd_plugin_install(spec: str, *, enable: bool = False) -> int:
    from ami.lifecycle import install_plugin

    cfg = Config()
    result = install_plugin(
        spec,
        plugins_dir=cfg.plugins_dir,
        enable=enable,
        config_path=get_config_filepath() if enable else None,
    )
    print(result.message)
    return 0 if result.ok else 1


def _release_store():
    from ami.lifecycle import ReleaseStore

    cfg = Config()
    return ReleaseStore(cfg.releases_dir, source_repo=cfg.repo_root)


def cmd_release_status() -> int:
    print(_release_store().status())
    return 0


def cmd_release_list() -> int:
    store = _release_store()
    tags = store.list_tags()
    cur = store.current_tag()
    for t in tags:
        mark = " *" if t == cur else ""
        print(f"{t}{mark}")
    if not tags:
        print("(no releases installed)")
    return 0


def cmd_release_install(tag: str, *, no_smoke: bool = False) -> int:
    result = _release_store().install_tag(tag, run_smoke=not no_smoke)
    print(result.message)
    return 0 if result.ok else 1


def cmd_release_activate(tag: str) -> int:
    result = _release_store().activate(tag)
    print(result.message)
    return 0 if result.ok else 1


def cmd_release_rollback() -> int:
    result = _release_store().rollback()
    print(result.message)
    return 0 if result.ok else 1


def cmd_doctor() -> int:
    cfg = Config()
    path = get_config_filepath()
    data = _load_raw_config(path)
    enabled = _enabled_list(data)
    print("AMI doctor")
    print(f"  config:     {path} ({'ok' if path.is_file() else 'MISSING'})")
    print(f"  data dir:   {cfg.data_dir}")
    print(f"  plugins:    {cfg.plugins_dir} ({'ok' if cfg.plugins_dir.is_dir() else 'missing'})")
    print(f"  releases:   {cfg.releases_dir}")
    print(f"  enabled:    {', '.join(enabled) or '(none)'}")
    print(f"  llm:        {(data.get('llm') or {}).get('backend', '(unset)')}")
    print(f"  stt:        {(data.get('stt') or {}).get('backend', '(unset)')}")
    speak = (data.get("routing") or {}).get("speak", "auto")
    print(f"  speak:      {speak}")
    print(f"  convos:     {cfg.convos_dir}")

    # last receipt
    last = None
    try:
        for sess in sorted(cfg.convos_dir.glob("*")):
            if not sess.is_dir():
                continue
            turns = sess / "turns"
            if not turns.is_dir():
                continue
            for tf in sorted(turns.glob("*.json"), reverse=True):
                last = tf
                break
            if last:
                break
    except OSError:
        last = None
    print(f"  last turn:  {last or '(none)'}")

    # release status one-liner
    try:
        store = _release_store()
        print(f"  release:    current={store.current_tag() or '(none)'} previous={store.previous_tag() or '(none)'}")
    except Exception as exc:
        print(f"  release:    error {exc}")

    # smoke import of live source
    try:
        import ami  # noqa: F401
        import ami.headspace.hub  # noqa: F401

        print("  import:     ok")
    except Exception as exc:
        print(f"  import:     FAIL {exc}")
        return 1
    return 0


def cmd_run(*, use_release: bool = False) -> int:
    """
    Launch ami.main.

    Default: current checkout / installed package on PYTHONPATH (dev).
    --release / AMI_USE_RELEASE=1: prepend ~/.ami/releases/CURRENT to sys.path
    so the activated release tree is preferred (appliance mode).
    """
    env = os.environ.copy()
    if use_release or env.get("AMI_USE_RELEASE", "").strip().lower() in ("1", "true", "yes"):
        cfg = Config()
        current = cfg.releases_dir / "CURRENT"
        if not current.is_dir():
            print(f"No CURRENT release at {current}. Install+activate first.", file=sys.stderr)
            return 1
        # Prefer release package root (contains `ami/`)
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(current) + (os.pathsep + prev if prev else "")
        print(f"Running from release CURRENT → {current}")
        return subprocess.call([sys.executable, "-m", "ami.main"], env=env)
    return subprocess.call([sys.executable, "-m", "ami.main"], env=env)


def cmd_directory_serve(
    *,
    host: str = "127.0.0.1",
    port: int = 4178,
    data: str = "",
    token: str = "",
    ttl: float = 3600.0,
) -> int:
    """Run Stronghold-ready neighbors directory (HTTP v1)."""
    from ami.neighbors_directory.__main__ import main as dir_main

    argv = ["--host", host, "--port", str(port), "--ttl", str(ttl)]
    if data:
        argv += ["--data", data]
    if token:
        argv += ["--token", token]
    return int(dir_main(argv))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ami.cli", description="AMI operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Config / paths / releases / import smoke")
    run_p = sub.add_parser("run", help="Run ami.main (full appliance)")
    run_p.add_argument(
        "--release",
        action="store_true",
        help="Prefer ~/.ami/releases/CURRENT on PYTHONPATH (or set AMI_USE_RELEASE=1)",
    )

    plug = sub.add_parser("plugin", help="Third-party + enabled_headspaces")
    plug_sub = plug.add_subparsers(dest="plugin_cmd", required=True)
    plug_sub.add_parser("list", help="List discovered plugins + enabled flag")
    en = plug_sub.add_parser("enable", help="Add name to enabled_headspaces")
    en.add_argument("name")
    dis = plug_sub.add_parser("disable", help="Remove name from enabled_headspaces")
    dis.add_argument("name")
    inst = plug_sub.add_parser("install", help="Install from git URL or user/repo[@tag]")
    inst.add_argument("spec")
    inst.add_argument("--enable", action="store_true", help="Also enable after install")
    val = plug_sub.add_parser("validate", help="Validate a plugin directory contract")
    val.add_argument("path")

    rel = sub.add_parser("release", help="Core release plane (install/activate/rollback)")
    rel_sub = rel.add_subparsers(dest="release_cmd", required=True)
    rel_sub.add_parser("status", help="Show CURRENT/PREVIOUS/installed")
    rel_sub.add_parser("list", help="List installed release tags")
    rinst = rel_sub.add_parser("install", help="Materialize git tag into releases/<tag>")
    rinst.add_argument("tag")
    rinst.add_argument("--no-smoke", action="store_true")
    ract = rel_sub.add_parser("activate", help="Point CURRENT at an installed tag")
    ract.add_argument("tag")
    rel_sub.add_parser("rollback", help="Activate PREVIOUS release")

    dirc = sub.add_parser("directory", help="Internet neighbors directory (Stronghold host)")
    dirc_sub = dirc.add_subparsers(dest="directory_cmd", required=True)
    dserve = dirc_sub.add_parser("serve", help="Run HTTP directory on LAN/cluster")
    dserve.add_argument("--host", default=os.environ.get("AMI_DIRECTORY_HOST", "127.0.0.1"))
    dserve.add_argument("--port", type=int, default=int(os.environ.get("AMI_DIRECTORY_PORT", "4178")))
    dserve.add_argument("--data", default=os.environ.get("AMI_DIRECTORY_DATA", ""))
    dserve.add_argument("--token", default=os.environ.get("AMI_NEIGHBORS_TOKEN", ""))
    dserve.add_argument("--ttl", type=float, default=float(os.environ.get("AMI_DIRECTORY_TTL", "3600")))

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "doctor":
        return cmd_doctor()
    if args.cmd == "run":
        return cmd_run(use_release=bool(getattr(args, "release", False)))
    if args.cmd == "plugin":
        if args.plugin_cmd == "list":
            return cmd_plugin_list()
        if args.plugin_cmd == "enable":
            return cmd_plugin_enable(args.name)
        if args.plugin_cmd == "disable":
            return cmd_plugin_disable(args.name)
        if args.plugin_cmd == "install":
            return cmd_plugin_install(args.spec, enable=bool(args.enable))
        if args.plugin_cmd == "validate":
            return cmd_plugin_validate(args.path)
    if args.cmd == "release":
        if args.release_cmd == "status":
            return cmd_release_status()
        if args.release_cmd == "list":
            return cmd_release_list()
        if args.release_cmd == "install":
            return cmd_release_install(args.tag, no_smoke=bool(args.no_smoke))
        if args.release_cmd == "activate":
            return cmd_release_activate(args.tag)
        if args.release_cmd == "rollback":
            return cmd_release_rollback()
    if args.cmd == "directory":
        if args.directory_cmd == "serve":
            return cmd_directory_serve(
                host=str(args.host),
                port=int(args.port),
                data=str(args.data or ""),
                token=str(args.token or ""),
                ttl=float(args.ttl),
            )
    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
