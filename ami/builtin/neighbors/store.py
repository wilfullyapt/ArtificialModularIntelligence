"""Durable peer store under a headspace filespace directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .models import Peer, PeerKind


class PeerStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path = self.root / "peers.json"

    def _load_raw(self) -> Dict[str, dict]:
        if not self._path.is_file():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _save_raw(self, data: Dict[str, dict]) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._path)

    def upsert(self, peer: Peer) -> None:
        data = self._load_raw()
        data[peer.peer_id] = peer.to_dict()
        self._save_raw(data)

    def get(self, peer_id: str) -> Optional[Peer]:
        raw = self._load_raw().get(peer_id)
        if not raw:
            return None
        return Peer.from_dict(raw)

    def list(self, kind: Optional[PeerKind] = None) -> List[Peer]:
        peers = [Peer.from_dict(v) for v in self._load_raw().values()]
        if kind is not None:
            peers = [p for p in peers if p.kind is kind]
        return sorted(peers, key=lambda p: p.display_name.lower())

    def remove(self, peer_id: str) -> bool:
        data = self._load_raw()
        if peer_id not in data:
            return False
        del data[peer_id]
        self._save_raw(data)
        return True
