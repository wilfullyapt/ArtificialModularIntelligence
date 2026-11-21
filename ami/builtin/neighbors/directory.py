"""Internet neighbor directory client (subscription or self-hosted)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import List, Optional, Protocol, Sequence

from .models import Peer, PeerKind


class DirectoryClient(Protocol):
    @property
    def enabled(self) -> bool: ...

    def list_peers(self) -> List[Peer]: ...


class StaticDirectory:
    """Test/dev directory backed by an in-memory peer list."""

    def __init__(self, peers: Optional[Sequence[Peer]] = None) -> None:
        self._peers = list(peers or [])

    @property
    def enabled(self) -> bool:
        return True

    def list_peers(self) -> List[Peer]:
        out: List[Peer] = []
        for peer in self._peers:
            if peer.kind is not PeerKind.INTERNET:
                peer = Peer(
                    peer_id=peer.peer_id,
                    display_name=peer.display_name,
                    kind=PeerKind.INTERNET,
                    endpoint=peer.endpoint,
                    capabilities=peer.capabilities,
                    last_seen=peer.last_seen,
                )
            out.append(peer)
        return out


def _as_internet(peer: Peer) -> Peer:
    if peer.kind is PeerKind.INTERNET:
        return peer
    return Peer(
        peer_id=peer.peer_id,
        display_name=peer.display_name,
        kind=PeerKind.INTERNET,
        endpoint=peer.endpoint,
        capabilities=peer.capabilities,
        last_seen=peer.last_seen,
    )


def peers_from_directory_payload(payload: object) -> List[Peer]:
    """Parse GET /v1/neighbors JSON into Peer list (kind forced internet)."""
    if isinstance(payload, dict):
        items = payload.get("peers") or []
    elif isinstance(payload, list):
        items = payload
    else:
        return []
    out: List[Peer] = []
    if not isinstance(items, list):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            out.append(_as_internet(Peer.from_dict(item)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


class InternetDirectory:
    """
    HTTP directory client for Stronghold / subscription hosts.

    - Disabled without base_url and without static_peers.
    - GET {base_url}/v1/neighbors with optional Bearer token.
    - POST {base_url}/v1/neighbors to register/heartbeat this node.
    - static_peers always merged (tests/dev overrides).
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        static_peers: Optional[Sequence[Peer]] = None,
        timeout: float = 5.0,
        opener: Optional[object] = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/") or None
        self.token = token
        self._static = list(static_peers or [])
        self.timeout = float(timeout)
        # injectable for tests: must provide .open(req, timeout=...) like urllib.request
        self._opener = opener

    @classmethod
    def disabled(cls) -> "InternetDirectory":
        return cls(base_url=None, token=None)

    @property
    def enabled(self) -> bool:
        return bool(self.base_url) or bool(self._static)

    def _headers(self) -> dict:
        headers = {"Accept": "application/json", "User-Agent": "ami-neighbors/1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _open(self, req: urllib.request.Request):
        if self._opener is not None:
            return self._opener.open(req, timeout=self.timeout)  # type: ignore[attr-defined]
        return urllib.request.urlopen(req, timeout=self.timeout)

    def list_peers(self) -> List[Peer]:
        if not self.enabled:
            return []
        peers: List[Peer] = [_as_internet(p) for p in self._static]
        if not self.base_url:
            return peers
        url = f"{self.base_url}/v1/neighbors"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with self._open(req) as resp:
                raw = resp.read().decode("utf-8")
                payload = json.loads(raw) if raw else {}
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ):
            return peers
        remote = peers_from_directory_payload(payload)
        by_id = {p.peer_id: p for p in peers}
        for p in remote:
            by_id[p.peer_id] = p
        return list(by_id.values())

    def register(self, peer: Peer) -> bool:
        """POST peer heartbeat to directory. Returns True on HTTP success."""
        if not self.base_url:
            return False
        body = json.dumps(_as_internet(peer).to_dict()).encode("utf-8")
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            f"{self.base_url}/v1/neighbors",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with self._open(req) as resp:
                return 200 <= getattr(resp, "status", 200) < 300
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return False
