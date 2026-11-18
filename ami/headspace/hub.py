"""Cross-headspace delegation hub — bounded self-referential tool loops."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Protocol

if TYPE_CHECKING:
    from .headspace import Headspace
    from .headspace_instructions import HeadspaceInstruction


class HeadspaceLike(Protocol):
    name: str

    def query(self, prompt: str) -> "HeadspaceInstruction": ...


@dataclass
class DelegationFrame:
    headspace: str
    prompt: str
    depth: int


@dataclass
class DelegationHub:
    """
    Shared registry so any Headspace can list peers and delegate work.

    Depth is process-wide for one Brain.query turn. Each delegate_to_headspace
    increments depth; max_depth stops loops (A→B→A→…).
    """

    max_depth: int = 3
    entry_headspace: str = "corespace"
    _registry: Dict[str, HeadspaceLike] = field(default_factory=dict)
    _depth: int = 0
    _stack: List[DelegationFrame] = field(default_factory=list)

    def reset_turn(self) -> None:
        self._depth = 0
        self._stack.clear()

    def register(self, name: str, headspace: HeadspaceLike) -> None:
        self._registry[name.lower()] = headspace

    def names(self) -> List[str]:
        return sorted(self._registry.keys())

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def stack(self) -> List[DelegationFrame]:
        return list(self._stack)

    def describe_menu(self, exclude: Optional[str] = None) -> str:
        """Human/LLM-readable menu of peer headspaces (hierarchy surface)."""
        lines = []
        for name in self.names():
            if exclude and name == exclude.lower():
                continue
            hs = self._registry[name]
            tool_names = []
            tools = getattr(hs, "tools", None)
            if tools is not None:
                try:
                    tool_names = [t.name for t in tools]
                except Exception:
                    tool_names = []
            tools_s = ", ".join(tool_names) if tool_names else "(no tools listed)"
            lines.append(f"- {name}: tools=[{tools_s}]")
        if not lines:
            return "No peer headspaces registered."
        return "Peer headspaces:\n" + "\n".join(lines)

    def delegate(self, target: str, prompt: str, *, from_headspace: str = "") -> str:
        """
        Run another headspace's query loop and return an observation string.

        Raises ValueError on unknown target or depth exceeded.
        """
        key = target.strip().lower()
        if key not in self._registry:
            known = ", ".join(self.names()) or "(none)"
            raise ValueError(f"Unknown headspace '{target}'. Known: {known}")

        if self._depth >= self.max_depth:
            raise ValueError(
                f"Delegation depth limit reached ({self.max_depth}). "
                f"Stack: {[f.headspace for f in self._stack]}"
            )

        # Prevent immediate pointless self-delegate (still allowed via longer cycles until max)
        if from_headspace and key == from_headspace.lower() and self._depth > 0:
            raise ValueError(
                f"Refusing nested self-delegate to '{key}' at depth {self._depth}."
            )

        self._depth += 1
        frame = DelegationFrame(headspace=key, prompt=prompt, depth=self._depth)
        self._stack.append(frame)
        try:
            result = self._registry[key].query(prompt)
            obs = getattr(result, "observation", None) or str(result)
            steps = getattr(result, "steps", None) or []
            return (
                f"[delegated→{key} depth={self._depth}] {obs}"
                + (f" | steps={len(steps)}" if steps else "")
            )
        finally:
            self._stack.pop()
            self._depth -= 1
