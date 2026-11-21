"""Phase E — directory HTTP + template contract + live client."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from ami.builtin.neighbors.directory import InternetDirectory, peers_from_directory_payload
from ami.builtin.neighbors.models import Peer, PeerKind
from ami.lifecycle.plugin_contract import validate_plugin_dir
from ami.neighbors_directory.server import serve_forever_background
from ami.neighbors_directory.store import DirectoryStore


def test_peers_from_directory_payload_forces_internet():
    peers = peers_from_directory_payload(
        {
            "api_version": "1",
            "peers": [
                {
                    "peer_id": "x1",
                    "display_name": "Remote",
                    "kind": "local",
                    "endpoint": "https://ex/x1",
                    "capabilities": ["mesh"],
                    "last_seen": 1.0,
                }
            ],
        }
    )
    assert len(peers) == 1
    assert peers[0].kind is PeerKind.INTERNET
    assert peers[0].peer_id == "x1"


def test_directory_store_ttl_and_persist(tmp_path: Path):
    path = tmp_path / "peers.json"
    now = time.time()
    store = DirectoryStore(path, ttl_seconds=60.0)
    store.upsert(
        Peer(
            peer_id="old",
            display_name="Old",
            kind=PeerKind.INTERNET,
            endpoint="https://e/old",
            last_seen=now - 10_000,
        )
    )
    store.upsert(
        Peer(
            peer_id="fresh",
            display_name="Fresh",
            kind=PeerKind.LOCAL,
            endpoint="https://e/fresh",
            last_seen=now,
        )
    )
    listed = store.list_peers()
    assert {p.peer_id for p in listed} == {"fresh"}
    assert listed[0].kind is PeerKind.INTERNET
    reloaded = DirectoryStore(path, ttl_seconds=3600)
    ids = {p.peer_id for p in reloaded.list_peers(include_stale=True)}
    assert "fresh" in ids


def test_directory_http_register_list_auth(tmp_path: Path):
    store = DirectoryStore(tmp_path / "d.json", ttl_seconds=3600)
    httpd, base = serve_forever_background(host="127.0.0.1", port=0, store=store, token="secret")
    try:
        bare = InternetDirectory(base_url=base, token=None, timeout=2.0)
        assert bare.list_peers() == []  # unauthorized → soft-fail empty

        client = InternetDirectory(base_url=base, token="secret", timeout=2.0)
        peer = Peer(
            peer_id="home-a",
            display_name="Home A",
            kind=PeerKind.LOCAL,
            endpoint="https://home-a",
            capabilities=("mesh", "voice"),
        )
        assert client.register(peer) is True
        peers = client.list_peers()
        assert any(p.peer_id == "home-a" and p.kind is PeerKind.INTERNET for p in peers)

        # health has no auth
        import urllib.request

        with urllib.request.urlopen(f"{base}/health", timeout=2) as resp:
            body = json.loads(resp.read().decode())
        assert body.get("ok") is True
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_public_headspace_template_validates():
    root = Path(__file__).resolve().parents[2]
    template = root / "templates" / "headspace"
    contract = validate_plugin_dir(template, require_toml=True)
    assert contract.ok, contract.errors
    assert contract.id == "demo_headspace"
    assert "headspace" in contract.exports
