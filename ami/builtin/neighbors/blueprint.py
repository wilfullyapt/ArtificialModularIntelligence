"""Flask blueprint for Neighbors — JSON peer list for the device web UI."""

from __future__ import annotations

from flask import jsonify

from ami.headspace import Blueprint, route


class NeighborsBlueprint(Blueprint):
    """HTTP surface for neighbor listing (read-only v1)."""

    @route("/")
    def index(self):
        return jsonify(
            {
                "headspace": "neighbors",
                "message": "AMI Neighbors — local mesh + optional internet directory",
                "routes": ["/status", "/peers"],
            }
        )

    @route("/status")
    def status(self):
        # Blueprint instances may not always have a live service; keep honest stub shape.
        return jsonify(
            {
                "headspace": "neighbors",
                "local_mesh": True,
                "note": "Full status available via Headspace tools when AI process is running",
            }
        )

    @route("/peers")
    def peers(self):
        return jsonify({"peers": [], "note": "Use Headspace list_neighbors for live mesh state"})
