"""P0 interaction receipts — Turn / Span trees persisted under ~/.ami/conversations."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return uuid.uuid4().hex[:12]


class SpanKind(str, Enum):
    ENTRY = "entry"
    THINK = "think"
    TOOL = "tool"
    ASK = "ask"
    DO = "do"
    SKILL = "skill"
    SPEAK = "speak"
    ERROR = "error"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    REFUSED = "refused"
    RUNNING = "running"


@dataclass
class Span:
    span_id: str
    kind: SpanKind
    headspace: str
    name: str = ""
    input_summary: str = ""
    output_summary: str = ""
    status: SpanStatus = SpanStatus.RUNNING
    parent_span_id: Optional[str] = None
    started_at: str = field(default_factory=_utc_now)
    ended_at: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "kind": self.kind.value if isinstance(self.kind, SpanKind) else self.kind,
            "headspace": self.headspace,
            "name": self.name,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "status": self.status.value if isinstance(self.status, SpanStatus) else self.status,
            "parent_span_id": self.parent_span_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Span":
        return cls(
            span_id=data["span_id"],
            kind=SpanKind(data["kind"]),
            headspace=data.get("headspace") or "",
            name=data.get("name") or "",
            input_summary=data.get("input_summary") or "",
            output_summary=data.get("output_summary") or "",
            status=SpanStatus(data.get("status") or SpanStatus.OK.value),
            parent_span_id=data.get("parent_span_id"),
            started_at=data.get("started_at") or _utc_now(),
            ended_at=data.get("ended_at"),
            data=data.get("data") or {},
        )


@dataclass
class TurnReceipt:
    """One human utterance → final speak, with a span tree for routing/return."""

    turn_id: str
    session_id: str
    human_text: str
    entry_headspace: str
    spans: List[Span] = field(default_factory=list)
    final_text: str = ""
    started_at: str = field(default_factory=_utc_now)
    finished_at: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.spans:
            root = Span(
                span_id=_short_id(),
                kind=SpanKind.ENTRY,
                headspace=self.entry_headspace,
                name="entry",
                input_summary=(self.human_text or "")[:240],
                status=SpanStatus.OK,
            )
            root.ended_at = root.started_at
            self.spans.append(root)

    @property
    def root_span_id(self) -> str:
        return self.spans[0].span_id

    def begin_span(
        self,
        *,
        kind: SpanKind,
        headspace: str,
        name: str = "",
        input_summary: str = "",
        parent_span_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        span = Span(
            span_id=_short_id(),
            kind=kind,
            headspace=headspace,
            name=name,
            input_summary=(input_summary or "")[:500],
            parent_span_id=parent_span_id if parent_span_id is not None else self.root_span_id,
            status=SpanStatus.RUNNING,
            data=data or {},
        )
        self.spans.append(span)
        return span.span_id

    def end_span(
        self,
        span_id: str,
        *,
        status: SpanStatus = SpanStatus.OK,
        output_summary: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        for span in self.spans:
            if span.span_id == span_id:
                span.status = status
                span.output_summary = (output_summary or "")[:1000]
                span.ended_at = _utc_now()
                if data:
                    span.data.update(data)
                return
        raise KeyError(f"Unknown span_id: {span_id}")

    @property
    def route_summary(self) -> str:
        """Human/debug one-liner of hop order (entry → asks/dos/tools → speak)."""
        parts: List[str] = []
        for span in self.spans:
            if span.kind == SpanKind.ENTRY:
                parts.append(span.headspace or "entry")
                continue
            if span.kind == SpanKind.SPEAK:
                parts.append("speak")
                continue
            label = span.headspace or span.name or span.kind.value
            if span.name and span.name not in (span.headspace, "entry", "ask_headspace", "do_headspace"):
                if span.kind in (SpanKind.TOOL, SpanKind.SKILL):
                    label = f"{span.headspace}.{span.name}" if span.headspace else span.name
            if span.kind == SpanKind.ASK:
                parts.append(f"ask:{label}")
            elif span.kind == SpanKind.DO:
                parts.append(f"do:{label}")
            elif span.kind == SpanKind.TOOL:
                parts.append(f"tool:{label}")
            elif span.kind == SpanKind.ERROR:
                parts.append(f"error:{label}")
            else:
                parts.append(f"{span.kind.value}:{label}")
        # de-dupe consecutive identical tokens
        compact: List[str] = []
        for p in parts:
            if not compact or compact[-1] != p:
                compact.append(p)
        return " → ".join(compact) if compact else "(empty)"

    def finish(self, final_text: str = "", route_extra: Optional[str] = None) -> None:
        self.final_text = final_text or self.final_text
        speak_id = self.begin_span(
            kind=SpanKind.SPEAK,
            headspace=self.entry_headspace,
            name="speak",
            input_summary="finalize",
            parent_span_id=self.root_span_id,
        )
        self.end_span(speak_id, status=SpanStatus.OK, output_summary=(self.final_text or "")[:500])
        self.finished_at = _utc_now()
        if route_extra:
            self.data["route_extra"] = route_extra

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "human_text": self.human_text,
            "entry_headspace": self.entry_headspace,
            "spans": [s.to_dict() for s in self.spans],
            "final_text": self.final_text,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "artifacts": list(self.artifacts),
            "route_summary": self.route_summary,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurnReceipt":
        turn = cls(
            turn_id=data["turn_id"],
            session_id=data["session_id"],
            human_text=data.get("human_text") or "",
            entry_headspace=data.get("entry_headspace") or "",
            spans=[],
            final_text=data.get("final_text") or "",
            started_at=data.get("started_at") or _utc_now(),
            finished_at=data.get("finished_at"),
            artifacts=list(data.get("artifacts") or []),
            data=data.get("data") or {},
        )
        turn.spans = [Span.from_dict(s) for s in data.get("spans") or []]
        if not turn.spans:
            turn.__post_init__()
        return turn


class InteractionStore:
    """
    Persist turns under <root>/<session_id>/turns/<turn_id>.json.

    Default root is Config().convos_dir when available.
    """

    def __init__(self, root: Optional[Path] = None):
        if root is None:
            from .config import Config

            root = Config().convos_dir
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def session_dir(self, session_id: str) -> Path:
        d = self.root / session_id / "turns"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def start_turn(
        self,
        *,
        session_id: str,
        human_text: str,
        entry_headspace: str = "corespace",
        turn_id: Optional[str] = None,
    ) -> TurnReceipt:
        return TurnReceipt(
            turn_id=turn_id or _short_id(),
            session_id=session_id,
            human_text=human_text,
            entry_headspace=entry_headspace,
        )

    def save_turn(self, turn: TurnReceipt) -> Path:
        path = self.session_dir(turn.session_id) / f"{turn.turn_id}.json"
        path.write_text(json.dumps(turn.to_dict(), indent=2), encoding="utf-8")
        return path

    def load_turn(self, session_id: str, turn_id: str) -> TurnReceipt:
        path = self.session_dir(session_id) / f"{turn_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return TurnReceipt.from_dict(data)
