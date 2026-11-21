"""Per-headspace skills — markdown procedures under filespace/skills/."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_simple_yaml_scalar(value: str) -> Any:
    v = value.strip()
    if not v:
        return ""
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        parts = []
        for p in inner.split(","):
            p = p.strip().strip("\"'")
            if p:
                parts.append(p)
        return parts
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        return int(v)
    except ValueError:
        pass
    return v


def _parse_frontmatter(block: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, rest = line.partition(":")
        data[key.strip()] = _parse_simple_yaml_scalar(rest)
    return data


@dataclass
class Skill:
    id: str
    body: str
    version: int = 1
    headspace: str = ""
    triggers: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    peers: List[str] = field(default_factory=list)
    status: str = "active"  # draft | active | retired
    source: str = "human"  # human | builtin | promoted | distilled
    path: Optional[Path] = None
    updated: str = ""
    raw_meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return (self.status or "").lower() == "active"

    @property
    def is_draft(self) -> bool:
        return (self.status or "").lower() == "draft"

    def to_prompt_block(self) -> str:
        trig = ", ".join(self.triggers) if self.triggers else "(none)"
        tools = ", ".join(self.tools) if self.tools else "(any)"
        return (
            f"### skill:{self.id} (v{self.version})\n"
            f"triggers: {trig}\n"
            f"preferred_tools: {tools}\n"
            f"{self.body.strip()}\n"
        )


def parse_skill_markdown(text: str, *, path: Optional[Path] = None) -> Skill:
    """Parse a skill markdown file with optional YAML-ish frontmatter."""
    text = text.lstrip("\ufeff")
    m = _FRONTMATTER_RE.match(text)
    if m:
        meta = _parse_frontmatter(m.group(1))
        body = m.group(2).strip()
    else:
        meta = {}
        body = text.strip()

    skill_id = str(meta.get("id") or (path.stem if path else "unnamed")).strip()
    triggers = meta.get("triggers") or []
    if isinstance(triggers, str):
        triggers = [t.strip() for t in triggers.split(",") if t.strip()]
    tools = meta.get("tools") or []
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.split(",") if t.strip()]
    peers = meta.get("peers") or []
    if isinstance(peers, str):
        peers = [p.strip() for p in peers.split(",") if p.strip()]

    version = meta.get("version", 1)
    try:
        version = int(version)
    except (TypeError, ValueError):
        version = 1

    return Skill(
        id=skill_id,
        body=body,
        version=version,
        headspace=str(meta.get("headspace") or ""),
        triggers=[str(t).lower() for t in triggers],
        tools=[str(t) for t in tools],
        peers=[str(p) for p in peers],
        status=str(meta.get("status") or "active").lower(),
        source=str(meta.get("source") or "human"),
        path=path,
        updated=str(meta.get("updated") or ""),
        raw_meta=meta,
    )


def match_skills(skills: Sequence[Skill], prompt: str, *, limit: int = 5) -> List[Skill]:
    """Return active skills whose triggers appear as substrings in prompt (case-insensitive)."""
    text = (prompt or "").lower()
    hits: List[Skill] = []
    for skill in skills:
        if not skill.is_active:
            continue
        if not skill.triggers:
            continue
        for trig in skill.triggers:
            if trig and trig in text:
                hits.append(skill)
                break
        if len(hits) >= limit:
            break
    return hits


def seed_default_skills(defaults_dir: Path, dest_skills_dir: Path) -> int:
    """
    Copy builtin default *.md skills into dest once (never overwrite user files).

    Returns number of files copied.
    """
    defaults_dir = Path(defaults_dir)
    dest_skills_dir = Path(dest_skills_dir)
    if not defaults_dir.is_dir():
        return 0
    dest_skills_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted(defaults_dir.glob("*.md")):
        dest = dest_skills_dir / src.name
        if dest.exists():
            continue
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        copied += 1
    return copied


def draft_skill_markdown(turn: Any, *, headspace: str = "") -> str:
    """Build a draft skill markdown from a TurnReceipt-like object."""
    human = getattr(turn, "human_text", "") or ""
    route = getattr(turn, "route_summary", "") or ""
    final = getattr(turn, "final_text", "") or ""
    entry = getattr(turn, "entry_headspace", "") or headspace or "unknown"
    hs = headspace or entry
    # crude trigger candidates from human text words
    words = re.findall(r"[a-zA-Z]{3,}", human.lower())
    # unique preserve order
    seen = set()
    triggers = []
    for w in words:
        if w not in seen and w not in ("the", "and", "for", "please", "with", "this"):
            seen.add(w)
            triggers.append(w)
        if len(triggers) >= 6:
            break
    if human and human.lower() not in triggers:
        # also keep a short phrase trigger
        phrase = " ".join(human.lower().split()[:4])
        if phrase and phrase not in triggers:
            triggers.insert(0, phrase)

    trig_yaml = "[" + ", ".join(f'"{t}"' for t in triggers) + "]"
    skill_id = f"draft-{hs}-{getattr(turn, 'turn_id', 'x')[:8]}"
    body = (
        f"# Draft skill from turn\n\n"
        f"Human: {human}\n\n"
        f"Route: {route}\n\n"
        f"Final: {final}\n\n"
        f"## Procedure\n\n"
        f"1. Re-read the route and preferred headspaces above.\n"
        f"2. Prefer the same ask/do pattern on similar requests.\n"
        f"3. Edit this draft, set status: active, then promote.\n"
    )
    return (
        f"---\n"
        f"id: {skill_id}\n"
        f"version: 1\n"
        f"headspace: {hs}\n"
        f"triggers: {trig_yaml}\n"
        f"tools: []\n"
        f"peers: []\n"
        f"status: draft\n"
        f"source: distilled\n"
        f"updated: {_utc_now()}\n"
        f"---\n\n"
        f"{body}"
    )


class SkillStore:
    """Filesystem skills under a headspace filespace/skills directory."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "drafts").mkdir(parents=True, exist_ok=True)

    def _load_file(self, path: Path) -> Optional[Skill]:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            return parse_skill_markdown(text, path=path)
        except Exception:
            return None

    def list_all(self, *, include_drafts: bool = False) -> List[Skill]:
        skills: List[Skill] = []
        for path in sorted(self.root.glob("*.md")):
            skill = self._load_file(path)
            if skill:
                skills.append(skill)
        if include_drafts:
            for path in sorted((self.root / "drafts").glob("*.md")):
                skill = self._load_file(path)
                if skill:
                    skills.append(skill)
        return skills

    def list_active(self) -> List[Skill]:
        return [s for s in self.list_all(include_drafts=False) if s.is_active]

    def list_drafts(self) -> List[Skill]:
        return [s for s in self.list_all(include_drafts=True) if s.is_draft]

    def match(self, prompt: str, *, limit: int = 5) -> List[Skill]:
        return match_skills(self.list_active(), prompt, limit=limit)

    def render_for_prompt(self, skills: Sequence[Skill]) -> str:
        if not skills:
            return ""
        blocks = [s.to_prompt_block() for s in skills]
        return "## Active skills (follow when relevant)\n\n" + "\n".join(blocks)

    def write_draft(self, markdown: str, *, suggested_id: str = "draft") -> Path:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", suggested_id).strip("-").lower() or "draft"
        path = self.root / "drafts" / f"{safe}.md"
        n = 1
        while path.exists():
            path = self.root / "drafts" / f"{safe}-{n}.md"
            n += 1
        path.write_text(markdown, encoding="utf-8")
        return path

    def promote_draft(self, draft_id: str) -> Path:
        """
        Move drafts/<id>.md → <id>.md and set status active.
        Raises FileNotFoundError if missing.
        """
        candidates = list((self.root / "drafts").glob(f"{draft_id}*.md"))
        # prefer exact stem match
        path = None
        for c in candidates:
            skill = self._load_file(c)
            if skill and skill.id == draft_id:
                path = c
                break
        if path is None:
            exact = self.root / "drafts" / f"{draft_id}.md"
            if exact.is_file():
                path = exact
        if path is None or not path.is_file():
            raise FileNotFoundError(f"Draft skill not found: {draft_id}")

        skill = self._load_file(path)
        if skill is None:
            raise ValueError(f"Unreadable draft: {path}")

        # rewrite status active
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(?m)^status:\s*\w+", "status: active", text, count=1)
        if "status: active" not in text:
            # inject into frontmatter if possible
            text = text.replace("---\n", "---\nstatus: active\n", 1)
        text = re.sub(r"(?m)^source:\s*\w+", "source: promoted", text, count=1)
        dest = self.root / f"{skill.id}.md"
        if dest.exists() and dest.resolve() != path.resolve():
            # version bump filename collision
            dest = self.root / f"{skill.id}-v{skill.version + 1}.md"
        dest.write_text(text, encoding="utf-8")
        try:
            path.unlink()
        except OSError:
            pass
        return dest
