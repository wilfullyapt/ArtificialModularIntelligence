"""Install third-party headspaces from git URL @ tag into ~/.ami/plugins."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .plugin_contract import PluginContract, validate_plugin_dir


@dataclass
class InstallResult:
    ok: bool
    message: str
    plugin_id: str = ""
    version: str = ""
    path: Optional[Path] = None
    contract: Optional[PluginContract] = None


def parse_install_spec(spec: str) -> Tuple[str, Optional[str]]:
    """
    Parse install specs:

      user/repo
      user/repo@v1.2.3
      https://github.com/user/repo.git@v1.2.3
      git@github.com:user/repo.git@v0.1.0
    """
    spec = (spec or "").strip()
    if not spec:
        raise ValueError("empty install spec")

    tag: Optional[str] = None
    base = spec
    if spec.count("@") >= 1:
        if spec.startswith("git@"):
            m = re.search(r"@([^@]+)$", spec)
            if m and "/" not in m.group(1) and ":" not in m.group(1):
                tag = m.group(1)
                base = spec[: m.start()]
        elif "://" in spec:
            left, _, right = spec.rpartition("@")
            if left and right and "/" not in right and ":" not in right:
                base, tag = left, right
        else:
            left, _, right = spec.rpartition("@")
            if left and right and "/" not in right:
                base, tag = left, right

    if "://" not in base and not base.startswith("git@"):
        if re.match(r"^[\w.-]+/[\w.-]+$", base):
            base = f"https://github.com/{base}.git"
        elif base.startswith("/") or base.startswith("."):
            # local path
            p = Path(base).resolve()
            if not p.exists():
                raise ValueError(f"local path not found: {base}")
            base = str(p)
        else:
            raise ValueError(f"unrecognized install spec: {spec}")

    return base, tag


def _run(cmd: list, *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)


def install_plugin(
    spec: str,
    *,
    plugins_dir: Path,
    enable: bool = False,
    config_path: Optional[Path] = None,
) -> InstallResult:
    """Clone repo, checkout tag if given, validate contract, install into plugins_dir/<id>."""
    try:
        url, tag = parse_install_spec(spec)
    except ValueError as exc:
        return InstallResult(ok=False, message=str(exc))

    plugins_dir = Path(plugins_dir)
    plugins_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ami-plugin-") as tmp:
        tmp_path = Path(tmp) / "src"
        clone_cmd = ["git", "clone", "--depth", "1"]
        if tag:
            clone_cmd += ["--branch", tag]
        clone_cmd += [url, str(tmp_path)]
        clone = _run(clone_cmd)
        if clone.returncode != 0:
            if tmp_path.exists():
                shutil.rmtree(tmp_path, ignore_errors=True)
            clone = _run(["git", "clone", url, str(tmp_path)])
            if clone.returncode != 0:
                return InstallResult(
                    ok=False,
                    message=f"git clone failed: {clone.stderr.strip() or clone.stdout.strip()}",
                )
            if tag:
                co = _run(["git", "checkout", tag], cwd=tmp_path)
                if co.returncode != 0:
                    return InstallResult(
                        ok=False,
                        message=f"git checkout {tag} failed: {co.stderr.strip() or co.stdout.strip()}",
                    )

        if not tag:
            desc = _run(["git", "describe", "--tags", "--abbrev=0"], cwd=tmp_path)
            if desc.returncode == 0:
                tag = desc.stdout.strip() or None

        contract = validate_plugin_dir(tmp_path, require_toml=False)
        if not contract.ok:
            return InstallResult(
                ok=False,
                message="contract validation failed: " + "; ".join(contract.errors),
                contract=contract,
            )

        dest = plugins_dir / contract.id
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(tmp_path, dest, ignore=shutil.ignore_patterns(".git"))
        (dest / ".ami-plugin-version").write_text(
            f"id={contract.id}\nversion={contract.version}\nsource={url}\ntag={tag or ''}\n",
            encoding="utf-8",
        )

        # Lightweight git repo so PluginRegistry third-party loader finds a tag + origin
        _run(["git", "init"], cwd=dest)
        _run(["git", "add", "-A"], cwd=dest)
        _run(["git", "config", "user.email", "ami@localhost"], cwd=dest)
        _run(["git", "config", "user.name", "AMI"], cwd=dest)
        _run(["git", "commit", "-m", f"install {contract.id} {contract.version}"], cwd=dest)
        ver_tag = contract.version if str(contract.version).startswith("v") else f"v{contract.version}"
        _run(["git", "tag", ver_tag], cwd=dest)
        if url:
            _run(["git", "remote", "add", "origin", url], cwd=dest)

        msg = f"installed {contract.id}@{contract.version} → {dest}"
        if contract.warnings:
            msg += " (warnings: " + "; ".join(contract.warnings) + ")"

        if enable and config_path is not None:
            from ami.cli import cmd_plugin_enable

            cmd_plugin_enable(contract.id, config_path=config_path)
            msg += " (enabled)"

        return InstallResult(
            ok=True,
            message=msg,
            plugin_id=contract.id,
            version=contract.version,
            path=dest,
            contract=contract,
        )
