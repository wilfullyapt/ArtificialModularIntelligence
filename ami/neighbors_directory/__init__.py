"""Stronghold-ready AMI neighbors directory (HTTP v1).

Deploy on household infra (Lamassu ops). Craft contract lives here and in
docs/NEIGHBORS_CONTRACT.md. Clients: AMI InternetDirectory, mobile-ami mesh.
"""

from __future__ import annotations

from .server import DirectoryApp, serve_directory
from .store import DirectoryStore

__all__ = ["DirectoryApp", "DirectoryStore", "serve_directory"]
