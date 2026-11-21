"""AMI core release plane: side-by-side tags under ~/.ami/releases with activate/rollback."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(cmd: list, *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)


@dataclass
class ReleaseResult:
    ok: bool
    message: str
    tag: str = ""
    path: Optional[Path] = None


class ReleaseStore:
    """
    Layout:

      <root>/
        CURRENT          # text: active tag
        PREVIOUS         # text: prior tag (for rollback)
        state.json       # metadata
        <tag>/           # full source tree at that tag
    """

    def __init__(self, root: Path, *, source_repo: Path):
        self.root = Path(root)
        self.source_repo = Path(source_repo)
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def current_file(self) -> Path:
        return self.root / "CURRENT"

    @property
    def previous_file(self) -> Path:
        return self.root / "PREVIOUS"

    @property
    def state_file(self) -> Path:
        return self.root / "state.json"

    def current_tag(self) -> Optional[str]:
        if self.current_file.is_file():
            t = self.current_file.read_text(encoding="utf-8").strip()
            return t or None
        return None

    def previous_tag(self) -> Optional[str]:
        if self.previous_file.is_file():
            t = self.previous_file.read_text(encoding="utf-8").strip()
            return t or None
        return None

    def list_tags(self) -> List[str]:
        return sorted(
            p.name for p in self.root.iterdir() if p.is_dir() and not p.name.startswith(".")
        )

    def release_dir(self, tag: str) -> Path:
        return self.root / tag

    def _write_state(self, **extra: Any) -> None:
        state: Dict[str, Any] = {}
        if self.state_file.is_file():
            try:
                state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                state = {}
        state.update(extra)
        state["updated_at"] = _utc_now()
        self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def install_tag(self, tag: str, *, run_smoke: bool = True) -> ReleaseResult:
        """Materialize source_repo at `tag` into releases/<tag>. Does not activate."""
        tag = tag.strip()
        if not tag:
            return ReleaseResult(ok=False, message="empty tag")

        if not (self.source_repo / ".git").exists():
            return ReleaseResult(ok=False, message=f"source is not a git repo: {self.source_repo}")

        probe = _run(["git", "rev-parse", "--verify", f"refs/tags/{tag}"], cwd=self.source_repo)
        if probe.returncode != 0:
            _run(["git", "fetch", "--tags", "--force"], cwd=self.source_repo)
            probe = _run(["git", "rev-parse", "--verify", f"refs/tags/{tag}"], cwd=self.source_repo)
            if probe.returncode != 0:
                return ReleaseResult(ok=False, message=f"tag not found: {tag}", tag=tag)

        dest = self.release_dir(tag)
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        archive_b = subprocess.run(
            ["git", "archive", "--format=tar", tag],
            cwd=str(self.source_repo),
            capture_output=True,
        )
        if archive_b.returncode != 0:
            return ReleaseResult(
                ok=False,
                message=f"git archive failed: {archive_b.stderr.decode(errors='replace')}",
                tag=tag,
            )

        with tarfile.open(fileobj=io.BytesIO(archive_b.stdout), mode="r:") as tf:
            tf.extractall(dest)

        if run_smoke:
            smoke = self.smoke_test(dest)
            if not smoke.ok:
                shutil.rmtree(dest, ignore_errors=True)
                return ReleaseResult(
                    ok=False,
                    message=f"smoke failed for {tag}: {smoke.message}",
                    tag=tag,
                )

        self._write_state(last_installed=tag)
        return ReleaseResult(ok=True, message=f"installed release {tag} → {dest}", tag=tag, path=dest)

    def smoke_test(self, release_path: Path) -> ReleaseResult:
        """Import-check the released tree without GUI/audio."""
        env_python = shutil.which("python3") or "python3"
        root = str(release_path)
        code = (
            "import sys; sys.path.insert(0, %r); "
            "import ami; import ami.core.interaction; import ami.headspace.hub; "
            "print('smoke-ok')"
        ) % root
        try:
            proc = subprocess.run(
                [env_python, "-c", code],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return ReleaseResult(ok=False, message="smoke timed out")
        if proc.returncode != 0:
            return ReleaseResult(
                ok=False,
                message=(proc.stderr or proc.stdout or "smoke import failed").strip()[:500],
            )
        if "smoke-ok" not in (proc.stdout or ""):
            return ReleaseResult(ok=False, message="smoke output missing smoke-ok")
        return ReleaseResult(ok=True, message="smoke ok", path=release_path)

    def activate(self, tag: str) -> ReleaseResult:
        tag = tag.strip()
        dest = self.release_dir(tag)
        if not dest.is_dir():
            return ReleaseResult(ok=False, message=f"release not installed: {tag}", tag=tag)

        smoke = self.smoke_test(dest)
        if not smoke.ok:
            return ReleaseResult(
                ok=False,
                message=f"refuse activate; smoke failed: {smoke.message}",
                tag=tag,
            )

        cur = self.current_tag()
        if cur and cur != tag:
            self.previous_file.write_text(cur + "\n", encoding="utf-8")
        self.current_file.write_text(tag + "\n", encoding="utf-8")
        self._write_state(current=tag, previous=self.previous_tag())
        return ReleaseResult(
            ok=True,
            message=f"activated {tag}" + (f" (previous={cur})" if cur and cur != tag else ""),
            tag=tag,
            path=dest,
        )

    def rollback(self) -> ReleaseResult:
        prev = self.previous_tag()
        if not prev:
            return ReleaseResult(ok=False, message="no PREVIOUS release to roll back to")
        cur = self.current_tag()
        result = self.activate(prev)
        if not result.ok:
            return result
        # After activate(prev), PREVIOUS became old current — good for multi-step rollback
        return ReleaseResult(
            ok=True,
            message=f"rollback to {prev}" + (f" (was {cur})" if cur else ""),
            tag=prev,
            path=result.path,
        )

    def status(self) -> str:
        lines = [
            f"releases root: {self.root}",
            f"current:  {self.current_tag() or '(none)'}",
            f"previous: {self.previous_tag() or '(none)'}",
            f"installed: {', '.join(self.list_tags()) or '(none)'}",
        ]
        cur = self.current_tag()
        if cur:
            lines.append(f"path: {self.release_dir(cur)}")
        return "\n".join(lines)
