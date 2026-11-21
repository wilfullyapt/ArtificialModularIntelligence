"""Neighbors headspace settings."""

from pydantic import Field

from ami.headspace.settings import BaseWidgetSettings


class NeighborsSettings(BaseWidgetSettings):
    """Settings for the neighbors plugin."""

    x: int = 20
    y: int = 20
    anchor: str = "nw"
    width: int = 360
    height: int = 220
    background_color: str = "black"
    highlight_color: str = "#7fdbff"
    lowlight_color: str = "#ffffff"

    display_name: str = Field(
        default="AMI",
        description="Human-readable name announced on the local mesh",
    )
    peer_id: str = Field(
        default="",
        description="Stable mesh peer id; empty = auto-generate and persist",
    )
    mesh_capabilities: str = Field(
        default="mesh,voice",
        description="Comma-separated capability tags announced on the mesh",
    )
    internet_directory_url: str = Field(
        default="",
        description="Optional internet neighbors directory base URL (subscription or Stronghold)",
    )
    internet_directory_token_env: str = Field(
        default="AMI_NEIGHBORS_TOKEN",
        description="Env var name holding optional directory bearer token",
    )
    mesh_transport: str = Field(
        default="memory",
        description="memory (in-process/dev) | udp (LAN broadcast, port mesh_port)",
    )
    mesh_port: int = Field(
        default=4177,
        description="UDP mesh port when mesh_transport=udp",
    )
    poll_on_list: bool = Field(
        default=True,
        description="When listing neighbors, poll local mesh first",
    )
