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


MESH_MAGIC = "AMI-MESH1"
DEFAULT_MESH_PORT = 4177


def encode_beacon(beacon: Beacon) -> bytes:
    """Serialize a beacon for UDP (JSON, UTF-8)."""
    import json

    payload = {
        "magic": MESH_MAGIC,
        "peer_id": beacon.peer_id,
        "display_name": beacon.display_name,
        "endpoint": beacon.endpoint,
        "capabilities": list(beacon.capabilities),
        "ts": beacon.ts,
    }
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def decode_beacon(data: bytes) -> Optional[Beacon]:
    """Parse a UDP payload into a Beacon, or None if invalid."""
    import json

    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("magic") != MESH_MAGIC:
        return None
    try:
        caps = payload.get("capabilities") or []
        if isinstance(caps, str):
            caps = [c.strip() for c in caps.split(",") if c.strip()]
        return Beacon(
            peer_id=str(payload["peer_id"]),
            display_name=str(payload.get("display_name") or payload["peer_id"]),
            endpoint=str(payload.get("endpoint") or ""),
            capabilities=tuple(caps),
            ts=float(payload.get("ts") or time.time()),
        )
    except (KeyError, TypeError, ValueError):
        return None


class UdpBroadcastMeshBus:
    """
    LAN mesh bus via UDP broadcast/multicast-style broadcast.

    Default port 4177. For unit tests, bind 127.0.0.1 and set
    broadcast_addr='127.0.0.1' so two sockets on the same host exchange beacons
    without needing real NIC broadcast permissions.
    """

    def __init__(
        self,
        *,
        port: int = DEFAULT_MESH_PORT,
        bind_addr: str = "0.0.0.0",
        broadcast_addr: str = "255.255.255.255",
        recv_buf: int = 65535,
    ) -> None:
        import socket

        self.port = port
        self.bind_addr = bind_addr
        self.broadcast_addr = broadcast_addr
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except OSError:
            pass
        self._sock.bind((bind_addr, port))
        self._sock.setblocking(False)
        self._recv_buf = recv_buf
        self._inbox: List[Beacon] = []

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def publish(self, beacon: Beacon) -> None:
        packet = encode_beacon(beacon)
        try:
            self._sock.sendto(packet, (self.broadcast_addr, self.port))
        except OSError:
            # Fall back to loopback so desk/dev still announces somewhere
            try:
                self._sock.sendto(packet, ("127.0.0.1", self.port))
            except OSError:
                pass

    def _drain(self) -> None:
        import socket

        while True:
            try:
                data, _addr = self._sock.recvfrom(self._recv_buf)
            except BlockingIOError:
                break
            except OSError:
                break
            beacon = decode_beacon(data)
            if beacon is not None:
                self._inbox.append(beacon)

    def collect(self, since: float) -> List[Beacon]:
        self._drain()
        matched = [b for b in self._inbox if b.ts >= since]
        # Keep recent inbox (last 5 minutes) to allow multi-poll
        cutoff = time.time() - 300
        self._inbox = [b for b in self._inbox if b.ts >= cutoff]
        return matched


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
