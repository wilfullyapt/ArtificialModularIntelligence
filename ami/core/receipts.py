"""List and load turn receipts from ~/.ami/conversations (debug / Flask)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReceiptSummary:
    session_id: str
    turn_id: str
    path: Path
    human_text: str = ""
    final_text: str = ""
    route_summary: str = ""
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "path": str(self.path),
            "human_text": self.human_text,
            "final_text": self.final_text,
            "route_summary": self.route_summary,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def list_receipts(convos_dir: Path, *, limit: int = 50) -> List[ReceiptSummary]:
    """Newest-first receipt summaries under convos_dir/<session>/turns/*.json."""
    convos_dir = Path(convos_dir)
    if not convos_dir.is_dir():
        return []
    items: List[ReceiptSummary] = []
    for sess in convos_dir.iterdir():
        if not sess.is_dir():
            continue
        turns = sess / "turns"
        if not turns.is_dir():
            continue
        for path in turns.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            items.append(
                ReceiptSummary(
                    session_id=str(data.get("session_id") or sess.name),
                    turn_id=str(data.get("turn_id") or path.stem),
                    path=path,
                    human_text=str(data.get("human_text") or "")[:200],
                    final_text=str(data.get("final_text") or "")[:200],
                    route_summary=str(data.get("route_summary") or ""),
                    started_at=str(data.get("started_at") or ""),
                    finished_at=str(data.get("finished_at") or ""),
                )
            )
    items.sort(key=lambda r: r.started_at or r.path.name, reverse=True)
    return items[:limit]


def load_receipt(convos_dir: Path, session_id: str, turn_id: str) -> Optional[Dict[str, Any]]:
    path = Path(convos_dir) / session_id / "turns" / f"{turn_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
