"""Cross-headspace delegation hub — ask/do verbs, receipts, depth guards."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

if TYPE_CHECKING:
    from ..core.interaction import TurnReceipt
    from .headspace_instructions import HeadspaceInstruction


class HeadspaceLike(Protocol):
    name: str

    def query(self, prompt: str) -> "HeadspaceInstruction": ...


@dataclass
class DelegationFrame:
    headspace: str
    prompt: str
    depth: int
    kind: str = "do"


@dataclass
class PeerResult:
    """Structured return from ask/do (observation + receipt linkage)."""

    ok: bool
    observation: str
    target: str
    kind: str  # ask | do
    span_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None
    steps: int = 0

    def as_tool_string(self) -> str:
        status = "ok" if self.ok else "error"
        arrow = f"{self.kind}→{self.target}"
        base = f"[{arrow} {status}] {self.observation}"
        if self.steps:
            base += f" | steps={self.steps}"
        if self.span_ids:
            base += f" | spans={len(self.span_ids)}"
        if self.error and not self.ok:
            base += f" | err={self.error}"
        return base


@dataclass
class DelegationHub:
    """
    Shared registry so any Headspace can list peers and ask/do work.

    Depth is process-wide for one Brain.query turn. Each ask/do increments
    depth; max_depth stops loops (A→B→A→…).

    Optional TurnReceipt (bind_turn) records span trees for routing/return.
    """

    max_depth: int = 3
    max_steps: int = 24
    entry_headspace: str = "corespace"
    _registry: Dict[str, HeadspaceLike] = field(default_factory=dict)
    _depth: int = 0
    _steps_used: int = 0
    _stack: List[DelegationFrame] = field(default_factory=list)
    _turn: Optional["TurnReceipt"] = None
    _current_parent_span_id: Optional[str] = None

    def reset_turn(self) -> None:
        self._depth = 0
        self._steps_used = 0
        self._stack.clear()
        self._turn = None
        self._current_parent_span_id = None

    def bind_turn(self, turn: Optional["TurnReceipt"]) -> None:
        """Attach a TurnReceipt so ask/do hops emit spans."""
        self._turn = turn
        if turn is not None and turn.spans:
            self._current_parent_span_id = turn.root_span_id
        else:
            self._current_parent_span_id = None

    @property
    def turn(self) -> Optional["TurnReceipt"]:
        return self._turn

    def register(self, name: str, headspace: HeadspaceLike) -> None:
        self._registry[name.lower()] = headspace

    def names(self) -> List[str]:
        return sorted(self._registry.keys())

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def steps_used(self) -> int:
        return self._steps_used

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

    def _begin_peer_span(
        self,
        *,
        kind: str,
        target: str,
        prompt: str,
        name: str = "",
    ) -> Optional[str]:
        if self._turn is None:
            return None
        from ..core.interaction import SpanKind

        if kind == "ask":
            span_kind = SpanKind.ASK
            span_name = name or "ask_headspace"
        elif kind == "do":
            span_kind = SpanKind.DO
            span_name = name or "do_headspace"
        elif kind == "tool":
            span_kind = SpanKind.TOOL
            span_name = name or "call_tool"
        else:
            span_kind = SpanKind.DO
            span_name = name or kind
        return self._turn.begin_span(
            kind=span_kind,
            headspace=target,
            name=span_name,
            input_summary=prompt,
            parent_span_id=self._current_parent_span_id,
        )

    def _end_peer_span(
        self,
        span_id: Optional[str],
        *,
        ok: bool,
        observation: str,
        error: Optional[str] = None,
    ) -> None:
        if self._turn is None or span_id is None:
            return
        from ..core.interaction import SpanStatus

        self._turn.end_span(
            span_id,
            status=SpanStatus.OK if ok else SpanStatus.ERROR,
            output_summary=observation,
            data={"error": error} if error else None,
        )

    def _dispatch(
        self,
        target: str,
        prompt: str,
        *,
        kind: str,
        from_headspace: str = "",
    ) -> PeerResult:
        key = target.strip().lower()
        span_ids: List[str] = []

        if key not in self._registry:
            known = ", ".join(self.names()) or "(none)"
            msg = f"Unknown headspace '{target}'. Known: {known}"
            span_id = self._begin_peer_span(kind=kind, target=key or target, prompt=prompt)
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False,
                observation=msg,
                target=target,
                kind=kind,
                span_ids=span_ids,
                error=msg,
            )

        if self._depth >= self.max_depth:
            msg = (
                f"Delegation depth limit reached ({self.max_depth}). "
                f"Stack: {[f.headspace for f in self._stack]}"
            )
            span_id = self._begin_peer_span(kind=kind, target=key, prompt=prompt)
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False,
                observation=msg,
                target=key,
                kind=kind,
                span_ids=span_ids,
                error=msg,
            )

        if self._steps_used >= self.max_steps:
            msg = f"Shared step budget exhausted ({self.max_steps})."
            span_id = self._begin_peer_span(kind=kind, target=key, prompt=prompt)
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False,
                observation=msg,
                target=key,
                kind=kind,
                span_ids=span_ids,
                error=msg,
            )

        if from_headspace and key == from_headspace.lower() and self._depth > 0:
            msg = f"Refusing nested self-delegate to '{key}' at depth {self._depth}."
            span_id = self._begin_peer_span(kind=kind, target=key, prompt=prompt)
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False,
                observation=msg,
                target=key,
                kind=kind,
                span_ids=span_ids,
                error=msg,
            )

        span_id = self._begin_peer_span(kind=kind, target=key, prompt=prompt)
        if span_id:
            span_ids.append(span_id)

        self._depth += 1
        self._steps_used += 1
        frame = DelegationFrame(headspace=key, prompt=prompt, depth=self._depth, kind=kind)
        self._stack.append(frame)
        prev_parent = self._current_parent_span_id
        if span_id:
            self._current_parent_span_id = span_id

        # Kind is recorded on the span; keep the user/task text clean for tools & tests.
        # (LLM entry preambles can teach ask vs do at the entry headspace.)
        run_prompt = prompt

        try:
            result = self._registry[key].query(run_prompt)
            obs = getattr(result, "observation", None) or str(result)
            steps = getattr(result, "steps", None) or []
            n_steps = len(steps) if isinstance(steps, list) else 0
            self._steps_used += n_steps
            self._end_peer_span(span_id, ok=True, observation=str(obs))
            return PeerResult(
                ok=True,
                observation=str(obs),
                target=key,
                kind=kind,
                span_ids=span_ids,
                steps=n_steps,
            )
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False,
                observation=msg,
                target=key,
                kind=kind,
                span_ids=span_ids,
                error=msg,
            )
        finally:
            self._stack.pop()
            self._depth -= 1
            self._current_parent_span_id = prev_parent

    def ask(self, target: str, question: str, *, from_headspace: str = "") -> PeerResult:
        """Read/info hop — prefer no side effects (prompt-hinted)."""
        return self._dispatch(target, question, kind="ask", from_headspace=from_headspace)

    def do(self, target: str, task: str, *, from_headspace: str = "") -> PeerResult:
        """Action hop — target may mutate via tools."""
        return self._dispatch(target, task, kind="do", from_headspace=from_headspace)

    # Peer meta-tools that must not be invoked via direct RPC (re-entrancy).
    META_TOOL_NAMES = frozenset(
        {
            "ask_headspace",
            "do_headspace",
            "delegate_to_headspace",
            "call_headspace_tool",
            "list_headspace_tools",
            "list_peer_headspaces",
        }
    )

    def list_tools(self, target: str, *, exclude_meta: bool = True) -> PeerResult:
        """List tool names on a registered headspace (no agent loop)."""
        key = target.strip().lower()
        if key not in self._registry:
            known = ", ".join(self.names()) or "(none)"
            msg = f"Unknown headspace '{target}'. Known: {known}"
            return PeerResult(ok=False, observation=msg, target=target, kind="tool", error=msg)
        hs = self._registry[key]
        tools = getattr(hs, "tools", None) or []
        names = []
        try:
            for t in tools:
                name = getattr(t, "name", None) or str(t)
                if exclude_meta and name in self.META_TOOL_NAMES:
                    continue
                # also skip skill meta
                if exclude_meta and name in ("list_skills", "promote_skill_draft"):
                    continue
                names.append(name)
        except Exception as exc:
            msg = f"Failed listing tools: {exc}"
            return PeerResult(ok=False, observation=msg, target=key, kind="tool", error=msg)
        obs = f"tools for {key}: " + (", ".join(names) if names else "(none)")
        return PeerResult(ok=True, observation=obs, target=key, kind="tool", steps=0)

    def call_tool(
        self,
        target: str,
        tool_name: str,
        args: Any = None,
        *,
        from_headspace: str = "",
    ) -> PeerResult:
        """
        Direct tool RPC — invoke a peer @ami_tool without a nested agent loop.

        args: dict or JSON object string.
        """
        import json
        from typing import Any as _Any  # local; module already has typing

        key = target.strip().lower()
        tname = (tool_name or "").strip()
        span_ids: List[str] = []
        input_summary = f"{tname}({args!r})"[:500]

        if key not in self._registry:
            known = ", ".join(self.names()) or "(none)"
            msg = f"Unknown headspace '{target}'. Known: {known}"
            span_id = self._begin_peer_span(
                kind="tool", target=key or target, prompt=input_summary, name=tname or "call_tool"
            )
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False, observation=msg, target=target, kind="tool", span_ids=span_ids, error=msg
            )

        if tname in self.META_TOOL_NAMES:
            msg = f"Direct RPC refused for peer meta-tool '{tname}'. Use ask/do or domain tools."
            span_id = self._begin_peer_span(
                kind="tool", target=key, prompt=input_summary, name=tname
            )
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False, observation=msg, target=key, kind="tool", span_ids=span_ids, error=msg
            )

        if self._steps_used >= self.max_steps:
            msg = f"Shared step budget exhausted ({self.max_steps})."
            span_id = self._begin_peer_span(
                kind="tool", target=key, prompt=input_summary, name=tname
            )
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False, observation=msg, target=key, kind="tool", span_ids=span_ids, error=msg
            )

        # Parse args
        parsed: Dict = {}
        if args is None or args == "":
            parsed = {}
        elif isinstance(args, dict):
            parsed = args
        elif isinstance(args, str):
            try:
                loaded = json.loads(args)
                if not isinstance(loaded, dict):
                    raise ValueError("args JSON must be an object")
                parsed = loaded
            except (json.JSONDecodeError, ValueError) as exc:
                msg = f"Invalid args JSON: {exc}"
                span_id = self._begin_peer_span(
                    kind="tool", target=key, prompt=input_summary, name=tname
                )
                if span_id:
                    span_ids.append(span_id)
                self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
                return PeerResult(
                    ok=False, observation=msg, target=key, kind="tool", span_ids=span_ids, error=msg
                )
        else:
            msg = f"args must be dict or JSON string, got {type(args).__name__}"
            return PeerResult(ok=False, observation=msg, target=key, kind="tool", error=msg)

        hs = self._registry[key]
        tools = getattr(hs, "tools", None) or []
        tool = None
        try:
            tool = next((t for t in tools if getattr(t, "name", None) == tname), None)
        except Exception:
            tool = None
        if tool is None:
            available = []
            try:
                available = [
                    t.name
                    for t in tools
                    if getattr(t, "name", None) and t.name not in self.META_TOOL_NAMES
                ]
            except Exception:
                pass
            msg = f"Tool '{tname}' not found on '{key}'. Available: {', '.join(available) or '(none)'}"
            span_id = self._begin_peer_span(
                kind="tool", target=key, prompt=input_summary, name=tname or "missing"
            )
            if span_id:
                span_ids.append(span_id)
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False, observation=msg, target=key, kind="tool", span_ids=span_ids, error=msg
            )

        span_id = self._begin_peer_span(
            kind="tool", target=key, prompt=input_summary, name=tname
        )
        if span_id:
            span_ids.append(span_id)

        self._steps_used += 1
        prev_parent = self._current_parent_span_id
        if span_id:
            self._current_parent_span_id = span_id
        try:
            method = tool.method
            raw = method(**parsed) if parsed else method()
            # HeadspaceInstruction → observation string
            if hasattr(raw, "observation"):
                obs = str(getattr(raw, "observation"))
            else:
                obs = str(raw)
            self._end_peer_span(span_id, ok=True, observation=obs)
            return PeerResult(
                ok=True,
                observation=obs,
                target=key,
                kind="tool",
                span_ids=span_ids,
                steps=1,
            )
        except TypeError as exc:
            msg = f"Tool arg error: {exc}"
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False, observation=msg, target=key, kind="tool", span_ids=span_ids, error=msg
            )
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            self._end_peer_span(span_id, ok=False, observation=msg, error=msg)
            return PeerResult(
                ok=False, observation=msg, target=key, kind="tool", span_ids=span_ids, error=msg
            )
        finally:
            self._current_parent_span_id = prev_parent

    def delegate(self, target: str, prompt: str, *, from_headspace: str = "") -> str:
        """
        Backward-compatible deep delegate (do-path).

        Returns tool-string. Raises ValueError on unknown/depth/self/budget
        so older callers and tests keep working.
        """
        result = self.do(target, prompt, from_headspace=from_headspace)
        err = result.error or ""
        if not result.ok and (
            "Unknown headspace" in err
            or "depth limit" in err
            or "self-delegate" in err
            or "step budget" in err
        ):
            raise ValueError(err)
        # Preserve older string shape for success
        if result.ok:
            base = f"[delegated→{result.target} depth={self._depth + 1}] {result.observation}"
            if result.steps:
                base += f" | steps={result.steps}"
            return base
        return result.as_tool_string()
