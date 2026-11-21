"""In-memory + optional JSON file peer directory store."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ami.builtin.neighbors.models import Peer, PeerKind


class DirectoryStore:
    """Authoritative peer list for internet neighbors directory."""

    def __init__(self, path: Optional[Path] = None, *, ttl_seconds: float = 3600.0) -> None:
        self.path = Path(path) if path else None
        self.ttl_seconds = float(ttl_seconds)
        self._lock = threading.RLock()
        self._peers: Dict[str, Peer] = {}
        if self.path and self.path.is_file():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        items = raw.get("peers") if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                peer = Peer.from_dict(item)
            except (KeyError, TypeError, ValueError):
                continue
            if peer.kind is not PeerKind.INTERNET:
                peer = Peer(
                    peer_id=peer.peer_id,
                    display_name=peer.display_name,
                    kind=PeerKind.INTERNET,
                    endpoint=peer.endpoint,
                    capabilities=peer.capabilities,
                    last_seen=peer.last_seen,
                )
            self._peers[peer.peer_id] = peer

    def _persist(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"peers": [p.to_dict() for p in self.list_peers(include_stale=True)]}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def upsert(self, peer: Peer) -> Peer:
        with self._lock:
            ls = float(peer.last_seen) if peer.last_seen else time.time()
            peer = Peer(
                peer_id=peer.peer_id,
                display_name=peer.display_name,
                kind=PeerKind.INTERNET,
                endpoint=peer.endpoint,
                capabilities=peer.capabilities,
                last_seen=ls,
            )
            self._peers[peer.peer_id] = peer
            self._persist()
            return peer

    def remove(self, peer_id: str) -> bool:
        with self._lock:
            existed = peer_id in self._peers
            self._peers.pop(peer_id, None)
            if existed:
                self._persist()
            return existed

    def get(self, peer_id: str) -> Optional[Peer]:
        with self._lock:
            return self._peers.get(peer_id)

    def list_peers(self, *, include_stale: bool = False) -> List[Peer]:
        now = time.time()
        with self._lock:
            out: List[Peer] = []
            stale_ids: List[str] = []
            for pid, peer in self._peers.items():
                age = now - float(peer.last_seen or 0.0)
                if not include_stale and self.ttl_seconds > 0 and age > self.ttl_seconds:
                    stale_ids.append(pid)
                    continue
                out.append(peer)
            for pid in stale_ids:
                self._peers.pop(pid, None)
            if stale_ids:
                self._persist()
            return sorted(out, key=lambda p: (p.display_name.lower(), p.peer_id))

    def snapshot_dict(self) -> Dict[str, Any]:
        return {
            "api_version": "1",
            "peers": [p.to_dict() for p in self.list_peers()],
        }
