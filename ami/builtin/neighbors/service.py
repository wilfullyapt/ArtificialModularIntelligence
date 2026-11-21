"""Neighbors orchestration: local mesh + internet directory + durable store."""

from __future__ import annotations

from typing import List, Literal, Optional

from .directory import DirectoryClient
from .fabric import LocalMeshFabric
from .models import Peer, PeerKind, merge_peers
from .store import PeerStore

Scope = Literal["local", "internet", "all"]


class NeighborsService:
    def __init__(
        self,
        *,
        store: PeerStore,
        fabric: LocalMeshFabric,
        directory: DirectoryClient,
    ) -> None:
        self.store = store
        self.fabric = fabric
        self.directory = directory

    def announce(self) -> Peer:
        beacon = self.fabric.announce()
        self_peer = Peer(
            peer_id=self.fabric.peer_id,
            display_name=self.fabric.display_name,
            kind=PeerKind.LOCAL,
            endpoint=self.fabric.endpoint,
            capabilities=self.fabric.capabilities,
        )
        # Do not store self as a neighbor; announce only.
        _ = beacon
        return self_peer

    def sync(self) -> List[Peer]:
        local = self.fabric.poll()
        for peer in local:
            self.store.upsert(peer)
        if self.directory.enabled:
            for peer in self.directory.list_peers():
                self.store.upsert(peer)
        return self.list_neighbors("all")

    def list_neighbors(self, scope: Scope = "all") -> List[Peer]:
        # Prefer live fabric snapshot merged with store + directory
        live_local = self.fabric.snapshot()
        if not live_local:
            live_local = self.fabric.poll()
        stored_local = self.store.list(kind=PeerKind.LOCAL)
        local = merge_peers(stored_local, live_local)

        internet: List[Peer] = []
        if self.directory.enabled:
            internet = list(self.directory.list_peers())
        stored_net = self.store.list(kind=PeerKind.INTERNET)
        internet = merge_peers(stored_net, internet)

        if scope == "local":
            return local
        if scope == "internet":
            return internet
        return merge_peers(local, internet)

    def describe(self, peer_id_or_name: str) -> Optional[Peer]:
        key = peer_id_or_name.strip().lower()
        for peer in self.list_neighbors("all"):
            if peer.peer_id.lower() == key or peer.display_name.lower() == key:
                return peer
        return self.store.get(peer_id_or_name)

    def set_display_name(self, name: str) -> str:
        self.fabric.set_display_name(name)
        return self.fabric.display_name

    def status(self) -> dict:
        peers = self.list_neighbors("all")
        return {
            "peer_id": self.fabric.peer_id,
            "display_name": self.fabric.display_name,
            "local_mesh": True,
            "internet_directory": bool(self.directory.enabled),
            "local_count": len([p for p in peers if p.kind is PeerKind.LOCAL]),
            "internet_count": len([p for p in peers if p.kind is PeerKind.INTERNET]),
            "endpoint": self.fabric.endpoint,
            "capabilities": list(self.fabric.capabilities),
        }
