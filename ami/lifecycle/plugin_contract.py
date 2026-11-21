"""Plugin contract validation for third-party headspaces."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


REQUIRED_EXPORTS = frozenset({"headspace"})  # at minimum
ALLOWED_EXPORTS = frozenset({"headspace", "gui", "blueprint"})


@dataclass
class PluginContract:
    id: str
    version: str
    ami_api_min: str = "0.1"
    exports: List[str] = field(default_factory=lambda: ["headspace"])
    source: str = "plugin.toml"
    path: Optional[Path] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse_simple_toml(text: str) -> Dict[str, Any]:
    """Minimal TOML-ish parser for flat string/list keys (no nested tables required)."""
    data: Dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, rest = line.partition("=")
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            items = []
            if inner:
                for part in inner.split(","):
                    p = part.strip().strip("\"'")
                    if p:
                        items.append(p)
            data[key] = items
        else:
            data[key] = rest.strip().strip("\"'")
    return data


def load_plugin_toml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return _parse_simple_toml(text)


def _ast_exports_init(init_path: Path) -> Tuple[List[str], List[str]]:
    """Return (found_export_names, errors) from __init__.py without importing."""
    errors: List[str] = []
    found: List[str] = []
    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    except SyntaxError as exc:
        return [], [f"__init__.py syntax error: {exc}"]

    assigned: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            assigned.add(node.name)
        elif isinstance(node, ast.FunctionDef):
            assigned.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                assigned.add(name)
    for export in ("Headspace", "GUI", "Blueprint", "EXAMPLES", "__version__"):
        if export in assigned:
            found.append(export)
    return found, errors


def validate_plugin_dir(plugin_dir: Path, *, require_toml: bool = False) -> PluginContract:
    """
    Validate a headspace package directory.

    Prefer plugin.toml; fall back to __init__ conventions for legacy plugins.
    """
    plugin_dir = Path(plugin_dir)
    errors: List[str] = []
    warnings: List[str] = []
    toml_path = plugin_dir / "plugin.toml"
    init_path = plugin_dir / "__init__.py"

    if not plugin_dir.is_dir():
        return PluginContract(id="", version="", errors=[f"not a directory: {plugin_dir}"])

    if not init_path.is_file():
        errors.append("missing __init__.py")

    meta: Dict[str, Any] = {}
    source = "convention"
    if toml_path.is_file():
        try:
            meta = load_plugin_toml(toml_path)
            source = "plugin.toml"
        except OSError as exc:
            errors.append(f"cannot read plugin.toml: {exc}")
    elif require_toml:
        errors.append("missing plugin.toml")
    else:
        warnings.append("no plugin.toml — using __init__ conventions only")

    pid = str(meta.get("id") or plugin_dir.name).strip()
    version = str(meta.get("version") or "").strip()
    ami_api_min = str(meta.get("ami_api_min") or "0.1").strip()
    exports_raw = meta.get("exports") or ["headspace"]
    if isinstance(exports_raw, str):
        exports = [exports_raw.lower()]
    else:
        exports = [str(x).lower() for x in exports_raw]

    if init_path.is_file():
        found, ast_errs = _ast_exports_init(init_path)
        errors.extend(ast_errs)
        # Map export tokens to symbols
        need_map = {
            "headspace": "Headspace",
            "gui": "GUI",
            "blueprint": "Blueprint",
        }
        for exp in exports:
            if exp not in ALLOWED_EXPORTS:
                errors.append(f"unknown export '{exp}' (allowed: {sorted(ALLOWED_EXPORTS)})")
                continue
            sym = need_map[exp]
            if sym not in found:
                errors.append(f"__init__.py must define/import {sym} (export={exp})")
        if "Headspace" not in found and "headspace" in exports:
            pass  # already errored
        if "EXAMPLES" not in found:
            warnings.append("EXAMPLES list not found in __init__.py (routing examples recommended)")
        if "__version__" not in found and not version:
            warnings.append("no __version__ in __init__.py and no version in plugin.toml")
            # try read __version__ via AST Constant
        if not version and "__version__" in found:
            # parse version string from AST
            try:
                tree = ast.parse(init_path.read_text(encoding="utf-8"))
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Name) and t.id == "__version__":
                                if isinstance(node.value, ast.Constant):
                                    version = str(node.value.value)
            except Exception:
                pass

    if not pid:
        errors.append("plugin id empty")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", pid or ""):
        errors.append(f"invalid plugin id '{pid}'")
    if not version:
        version = "0.0.0"
        warnings.append("version defaulted to 0.0.0")

    return PluginContract(
        id=pid,
        version=version,
        ami_api_min=ami_api_min,
        exports=exports,
        source=source,
        path=plugin_dir,
        errors=errors,
        warnings=warnings,
    )
