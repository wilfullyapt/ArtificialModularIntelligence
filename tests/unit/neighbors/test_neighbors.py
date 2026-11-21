"""Neighbors domain tests — local mesh + internet directory (no hardware)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ami.builtin.neighbors.directory import InternetDirectory, StaticDirectory
from ami.builtin.neighbors.fabric import InMemoryMeshBus, LocalMeshFabric
from ami.builtin.neighbors.models import Peer, PeerKind
from ami.builtin.neighbors.service import NeighborsService
from ami.builtin.neighbors.store import PeerStore


def test_peer_roundtrip_json(tmp_path: Path):
    store = PeerStore(tmp_path)
    peer = Peer(
        peer_id="ami-local-1",
        display_name="Kitchen AMI",
        kind=PeerKind.LOCAL,
        endpoint="udp://192.168.0.10:4177",
        capabilities=("mesh", "voice"),
    )
    store.upsert(peer)
    loaded = store.get("ami-local-1")
    assert loaded is not None
    assert loaded.display_name == "Kitchen AMI"
    assert loaded.kind is PeerKind.LOCAL
    assert "mesh" in loaded.capabilities


def test_local_mesh_discovers_peer_via_shared_bus():
    bus = InMemoryMeshBus()
    a = LocalMeshFabric(
        peer_id="device-a",
        display_name="A",
        bus=bus,
        capabilities=("mesh",),
    )
    b = LocalMeshFabric(
        peer_id="device-b",
        display_name="B",
        bus=bus,
        capabilities=("mesh", "hat"),
    )
    a.announce()
    b.announce()
    seen_by_a = a.poll()
    seen_by_b = b.poll()
    assert any(p.peer_id == "device-b" for p in seen_by_a)
    assert any(p.peer_id == "device-a" for p in seen_by_b)
    # never see self
    assert all(p.peer_id != "device-a" for p in seen_by_a)


def test_internet_directory_lists_remote_peers():
    directory = StaticDirectory(
        peers=[
            Peer(
                peer_id="net-1",
                display_name="Cousin House",
                kind=PeerKind.INTERNET,
                endpoint="https://neighbors.example/net-1",
                capabilities=("mesh",),
            )
        ]
    )
    peers = directory.list_peers()
    assert len(peers) == 1
    assert peers[0].kind is PeerKind.INTERNET
    assert peers[0].display_name == "Cousin House"


def test_neighbors_service_merges_local_and_internet(tmp_path: Path):
    bus = InMemoryMeshBus()
    fabric = LocalMeshFabric(
        peer_id="home-1",
        display_name="Home",
        bus=bus,
        capabilities=("mesh",),
    )
    other = LocalMeshFabric(
        peer_id="home-2",
        display_name="Shop",
        bus=bus,
        capabilities=("mesh",),
    )
    other.announce()

    directory = StaticDirectory(
        peers=[
            Peer(
                peer_id="net-9",
                display_name="Remote Friend",
                kind=PeerKind.INTERNET,
                endpoint="https://example/net-9",
                capabilities=("mesh",),
            )
        ]
    )
    svc = NeighborsService(
        store=PeerStore(tmp_path),
        fabric=fabric,
        directory=directory,
    )
    svc.sync()
    local_only = svc.list_neighbors(scope="local")
    internet_only = svc.list_neighbors(scope="internet")
    all_peers = svc.list_neighbors(scope="all")

    assert {p.peer_id for p in local_only} == {"home-2"}
    assert {p.peer_id for p in internet_only} == {"net-9"}
    assert {p.peer_id for p in all_peers} == {"home-2", "net-9"}


def test_neighbors_service_status_and_set_name(tmp_path: Path):
    bus = InMemoryMeshBus()
    fabric = LocalMeshFabric(
        peer_id="home-1",
        display_name="Home",
        bus=bus,
        capabilities=("mesh",),
    )
    svc = NeighborsService(
        store=PeerStore(tmp_path),
        fabric=fabric,
        directory=InternetDirectory.disabled(),
    )
    status = svc.status()
    assert status["peer_id"] == "home-1"
    assert status["display_name"] == "Home"
    assert status["local_mesh"] is True
    assert status["internet_directory"] is False

    svc.set_display_name("Living Room")
    assert svc.status()["display_name"] == "Living Room"


def test_disabled_internet_directory_is_empty():
    d = InternetDirectory.disabled()
    assert d.enabled is False
    assert d.list_peers() == []


def test_headspace_tools_list_and_announce(tmp_path: Path):
    """Tool surface (NeighborsTools) used by Headspace — headless, no PyQt."""
    from ami.builtin.neighbors.tools import NeighborsTools

    bus = InMemoryMeshBus()
    fabric = LocalMeshFabric(
        peer_id="kit-1",
        display_name="Kitchen",
        bus=bus,
        capabilities=("mesh", "voice"),
    )
    peer_fabric = LocalMeshFabric(
        peer_id="porch-1",
        display_name="Porch",
        bus=bus,
        capabilities=("mesh",),
    )
    peer_fabric.announce()

    tools = NeighborsTools(
        NeighborsService(
            store=PeerStore(tmp_path),
            fabric=fabric,
            directory=StaticDirectory(
                [
                    Peer(
                        peer_id="wan-1",
                        display_name="Internet Neighbor",
                        kind=PeerKind.INTERNET,
                        endpoint="https://example/wan-1",
                        capabilities=("mesh",),
                    )
                ]
            ),
        )
    )

    announced = tools.announce_presence()
    assert "Kitchen" in announced or "announced" in announced.lower()

    listing = tools.list_neighbors("all")
    assert "Porch" in listing
    assert "Internet Neighbor" in listing

    local = tools.list_neighbors("local")
    assert "Porch" in local
    assert "Internet Neighbor" not in local

    detail = tools.describe_neighbor("porch-1")
    assert "porch-1" in detail.lower() or "Porch" in detail

    st = tools.mesh_status()
    assert "kit-1" in st
