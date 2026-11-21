"""AMI operator CLI (Python-first).

Config SoR for plugins: ~/.ami/ami_config.yaml → enabled_headspaces: [list]

Usage:
  python -m ami.cli plugin list
  python -m ami.cli plugin enable <name>
  python -m ami.cli plugin disable <name>
  python -m ami.cli doctor
  python -m ami.cli run
"""

from __future__ import annotations

import argparse
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
    # Discover builtins + third-party without requiring IPC
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


def cmd_doctor() -> int:
    cfg = Config()
    path = get_config_filepath()
    data = _load_raw_config(path)
    enabled = _enabled_list(data)
    print("AMI doctor")
    print(f"  config:     {path} ({'ok' if path.is_file() else 'MISSING'})")
    print(f"  data dir:   {cfg.data_dir}")
    print(f"  plugins:    {cfg.plugins_dir} ({'ok' if cfg.plugins_dir.is_dir() else 'missing'})")
    print(f"  enabled:    {', '.join(enabled) or '(none)'}")
    print(f"  llm:        {(data.get('llm') or {}).get('backend', '(unset)')}")
    print(f"  stt:        {(data.get('stt') or {}).get('backend', '(unset)')}")
    speak = (data.get("routing") or {}).get("speak", "auto")
    print(f"  speak:      {speak}")
    convos = cfg.convos_dir
    print(f"  convos:     {convos}")
    return 0


def cmd_run() -> int:
    """Launch full AMI (three-process main)."""
    return subprocess.call([sys.executable, "-m", "ami.main"])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ami.cli", description="AMI operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Show config / paths / enabled headspaces")
    sub.add_parser("run", help="Run ami.main (full appliance)")

    plug = sub.add_parser("plugin", help="Manage enabled_headspaces")
    plug_sub = plug.add_subparsers(dest="plugin_cmd", required=True)
    plug_sub.add_parser("list", help="List discovered plugins + enabled flag")
    en = plug_sub.add_parser("enable", help="Add name to enabled_headspaces")
    en.add_argument("name")
    dis = plug_sub.add_parser("disable", help="Remove name from enabled_headspaces")
    dis.add_argument("name")

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "doctor":
        return cmd_doctor()
    if args.cmd == "run":
        return cmd_run()
    if args.cmd == "plugin":
        if args.plugin_cmd == "list":
            return cmd_plugin_list()
        if args.plugin_cmd == "enable":
            return cmd_plugin_enable(args.name)
        if args.plugin_cmd == "disable":
            return cmd_plugin_disable(args.name)
    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
