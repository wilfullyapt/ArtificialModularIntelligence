"""Neighbor peer model for AMI mesh + internet directory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Tuple
import time


class PeerKind(str, Enum):
    LOCAL = "local"
    INTERNET = "internet"


@dataclass(frozen=True)
class Peer:
    peer_id: str
    display_name: str
    kind: PeerKind
    endpoint: str = ""
    capabilities: Tuple[str, ...] = ()
    last_seen: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["capabilities"] = list(self.capabilities)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Peer":
        caps = data.get("capabilities") or []
        if isinstance(caps, str):
            caps = [c.strip() for c in caps.split(",") if c.strip()]
        kind_raw = data.get("kind", PeerKind.LOCAL.value)
        kind = PeerKind(kind_raw) if not isinstance(kind_raw, PeerKind) else kind_raw
        return cls(
            peer_id=str(data["peer_id"]),
            display_name=str(data.get("display_name") or data["peer_id"]),
            kind=kind,
            endpoint=str(data.get("endpoint") or ""),
            capabilities=tuple(caps),
            last_seen=float(data.get("last_seen") or time.time()),
        )


def merge_peers(*groups: Iterable[Peer]) -> list[Peer]:
    """Last write wins by peer_id."""
    by_id: dict[str, Peer] = {}
    for group in groups:
        for peer in group:
            by_id[peer.peer_id] = peer
    return sorted(by_id.values(), key=lambda p: (p.kind.value, p.display_name.lower()))
