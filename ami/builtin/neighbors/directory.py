"""Internet neighbor directory client (subscription or self-hosted)."""

from __future__ import annotations

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


class InternetDirectory:
    """
    HTTP directory client skeleton.

    v1: disabled without base_url; list_peers returns [] when disabled.
    Live HTTP fetch can land once Stronghold/subscription endpoint is scoped.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        static_peers: Optional[Sequence[Peer]] = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/") or None
        self.token = token
        self._static = list(static_peers or [])

    @classmethod
    def disabled(cls) -> "InternetDirectory":
        return cls(base_url=None, token=None)

    @property
    def enabled(self) -> bool:
        return bool(self.base_url) or bool(self._static)

    def list_peers(self) -> List[Peer]:
        if not self.enabled:
            return []
        # Placeholder for future GET {base_url}/v1/neighbors
        # Until then, optional static_peers supports config-driven internet neighbors.
        peers: List[Peer] = []
        for peer in self._static:
            if peer.kind is not PeerKind.INTERNET:
                peer = Peer(
                    peer_id=peer.peer_id,
                    display_name=peer.display_name,
                    kind=PeerKind.INTERNET,
                    endpoint=peer.endpoint,
                    capabilities=peer.capabilities,
                    last_seen=peer.last_seen,
                )
            peers.append(peer)
        return peers
