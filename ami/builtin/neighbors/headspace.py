"""Neighbors Headspace — local AMI mesh peers + optional internet neighbors."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from ami.headspace import Headspace, ami_tool

from .directory import InternetDirectory
from .fabric import (
    DEFAULT_MESH_PORT,
    InMemoryMeshBus,
    LocalMeshFabric,
    MeshBus,
    UdpBroadcastMeshBus,
)
from .service import NeighborsService
from .settings import NeighborsSettings
from .store import PeerStore
from .tools import NeighborsTools

# Shared default bus so multiple in-process AMI components can meet in dev/tests.
_DEFAULT_BUS = InMemoryMeshBus()


def _parse_caps(raw: str) -> tuple[str, ...]:
    parts = [p.strip() for p in (raw or "").split(",") if p.strip()]
    return tuple(parts) or ("mesh",)


def _build_bus(settings: NeighborsSettings, bus: Optional[MeshBus] = None) -> MeshBus:
    if bus is not None:
        return bus
    transport = (getattr(settings, "mesh_transport", None) or "memory").strip().lower()
    if transport == "udp":
        port = int(getattr(settings, "mesh_port", None) or DEFAULT_MESH_PORT)
        return UdpBroadcastMeshBus(port=port)
    return _DEFAULT_BUS


def build_neighbors_service(
    filespace: Path,
    settings: NeighborsSettings,
    *,
    bus: Optional[MeshBus] = None,
) -> NeighborsService:
    peer_id = (settings.peer_id or "").strip()
    id_file = filespace / "peer_id"
    if not peer_id:
        if id_file.is_file():
            peer_id = id_file.read_text(encoding="utf-8").strip()
        if not peer_id:
            peer_id = f"ami-{uuid.uuid4().hex[:12]}"
            id_file.write_text(peer_id, encoding="utf-8")
    else:
        id_file.write_text(peer_id, encoding="utf-8")

    fabric = LocalMeshFabric(
        peer_id=peer_id,
        display_name=settings.display_name or "AMI",
        bus=_build_bus(settings, bus),
        capabilities=_parse_caps(settings.mesh_capabilities),
    )
    token_env = settings.internet_directory_token_env or "AMI_NEIGHBORS_TOKEN"
    token = os.environ.get(token_env) or None
    base = (settings.internet_directory_url or "").strip() or None
    directory = (
        InternetDirectory(base_url=base, token=token)
        if base
        else InternetDirectory.disabled()
    )
    return NeighborsService(
        store=PeerStore(filespace),
        fabric=fabric,
        directory=directory,
    )


class NeighborsHeadspace(Headspace):
    """Discover local mesh AMI devices and optional internet neighbors."""

    settings_class = NeighborsSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = build_neighbors_service(self.filespace, self.settings)
        self._tools = NeighborsTools(self.service, poll_on_list=self.settings.poll_on_list)

    @ami_tool
    def list_neighbors(self, scope: str = "all"):
        """List AMI neighbors. scope is local, internet, or all."""
        return self._tools.list_neighbors(scope)

    @ami_tool
    def announce_presence(self):
        """Announce this AMI device on the local mesh so neighbors can discover it."""
        return self._tools.announce_presence()

    @ami_tool
    def mesh_status(self):
        """Report this device's mesh identity and neighbor counts."""
        return self._tools.mesh_status()

    @ami_tool
    def describe_neighbor(self, name_or_id: str):
        """Describe one neighbor by display name or peer id."""
        return self._tools.describe_neighbor(name_or_id)

    @ami_tool
    def set_neighbor_display_name(self, display_name: str):
        """Set the display name this AMI announces to local neighbors."""
        result = self._tools.set_neighbor_display_name(display_name)
        try:
            self.settings.display_name = self.service.fabric.display_name
            self.settings.save_to_file(self._settings_file)
        except Exception:
            pass
        return result
