"""Headless tool surface for Neighbors (no PyQt / LLM imports)."""

from __future__ import annotations

from .service import NeighborsService, Scope


class NeighborsTools:
    """Callable tool methods shared by the Headspace wrapper and unit tests."""

    def __init__(self, service: NeighborsService, *, poll_on_list: bool = True):
        self.service = service
        self.poll_on_list = poll_on_list

    def _format_peer_lines(self, scope: Scope) -> str:
        if self.poll_on_list:
            self.service.sync()
        peers = self.service.list_neighbors(scope)
        if not peers:
            return f"No {scope} neighbors found."
        lines = []
        for peer in peers:
            caps = ",".join(peer.capabilities) if peer.capabilities else "-"
            lines.append(
                f"- [{peer.kind.value}] {peer.display_name} ({peer.peer_id}) "
                f"endpoint={peer.endpoint or '-'} caps={caps}"
            )
        return f"{scope.title()} neighbors ({len(peers)}):\n" + "\n".join(lines)

    def list_neighbors(self, scope: str = "all") -> str:
        """List AMI neighbors. scope is local, internet, or all."""
        normalized = (scope or "all").strip().lower()
        if normalized not in ("local", "internet", "all"):
            return "Invalid scope. Use local, internet, or all."
        return self._format_peer_lines(normalized)  # type: ignore[arg-type]

    def announce_presence(self) -> str:
        """Announce this AMI device on the local mesh so neighbors can discover it."""
        self_peer = self.service.announce()
        return (
            f"Announced on local mesh as '{self_peer.display_name}' "
            f"(peer_id={self_peer.peer_id}, endpoint={self_peer.endpoint})."
        )

    def mesh_status(self) -> str:
        """Report this device's mesh identity and neighbor counts."""
        if self.poll_on_list:
            self.service.sync()
        st = self.service.status()
        return (
            f"peer_id={st['peer_id']} display_name={st['display_name']} "
            f"local_mesh={st['local_mesh']} internet_directory={st['internet_directory']} "
            f"local_count={st['local_count']} internet_count={st['internet_count']} "
            f"endpoint={st['endpoint']} capabilities={','.join(st['capabilities'])}"
        )

    def describe_neighbor(self, name_or_id: str) -> str:
        """Describe one neighbor by display name or peer id."""
        if self.poll_on_list:
            self.service.sync()
        peer = self.service.describe(name_or_id)
        if not peer:
            return f"Neighbor '{name_or_id}' not found. Try list_neighbors."
        caps = ",".join(peer.capabilities) if peer.capabilities else "-"
        return (
            f"{peer.display_name} id={peer.peer_id} kind={peer.kind.value} "
            f"endpoint={peer.endpoint or '-'} caps={caps} last_seen={peer.last_seen}"
        )

    def set_neighbor_display_name(self, display_name: str) -> str:
        """Set the display name this AMI announces to local neighbors."""
        name = self.service.set_display_name(display_name)
        return f"Display name set to '{name}'."
