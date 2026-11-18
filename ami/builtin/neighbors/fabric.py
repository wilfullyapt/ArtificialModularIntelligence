"""Local AMI mesh fabric — injectable transports (in-memory default for tests)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple

from .models import Peer, PeerKind


@dataclass
class Beacon:
    peer_id: str
    display_name: str
    endpoint: str
    capabilities: Tuple[str, ...]
    ts: float = field(default_factory=time.time)

    def to_peer(self) -> Peer:
        return Peer(
            peer_id=self.peer_id,
            display_name=self.display_name,
            kind=PeerKind.LOCAL,
            endpoint=self.endpoint,
            capabilities=self.capabilities,
            last_seen=self.ts,
        )


class MeshBus(Protocol):
    def publish(self, beacon: Beacon) -> None: ...
    def collect(self, since: float) -> List[Beacon]: ...


class InMemoryMeshBus:
    """Process-local bus so multiple fabrics can discover each other in tests."""

    def __init__(self) -> None:
        self._beacons: List[Beacon] = []

    def publish(self, beacon: Beacon) -> None:
        self._beacons.append(beacon)

    def collect(self, since: float) -> List[Beacon]:
        return [b for b in self._beacons if b.ts >= since]


class LocalMeshFabric:
    """Announce this AMI node and poll the bus for other local AMI peers."""

    def __init__(
        self,
        *,
        peer_id: str,
        display_name: str,
        bus: MeshBus,
        capabilities: Tuple[str, ...] = ("mesh",),
        endpoint: str = "",
    ) -> None:
        self.peer_id = peer_id
        self.display_name = display_name
        self.bus = bus
        self.capabilities = tuple(capabilities)
        self.endpoint = endpoint or f"ami-mesh://{peer_id}"
        self._last_poll = 0.0
        self._seen: Dict[str, Peer] = {}

    def set_display_name(self, name: str) -> None:
        self.display_name = name.strip() or self.display_name

    def announce(self) -> Beacon:
        beacon = Beacon(
            peer_id=self.peer_id,
            display_name=self.display_name,
            endpoint=self.endpoint,
            capabilities=self.capabilities,
            ts=time.time(),
        )
        self.bus.publish(beacon)
        return beacon

    def poll(self) -> List[Peer]:
        beacons = self.bus.collect(self._last_poll)
        self._last_poll = time.time()
        for beacon in beacons:
            if beacon.peer_id == self.peer_id:
                continue
            peer = beacon.to_peer()
            self._seen[peer.peer_id] = peer
        return list(self._seen.values())

    def snapshot(self) -> List[Peer]:
        return list(self._seen.values())
