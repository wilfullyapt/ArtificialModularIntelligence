---
id: neighbors-presence
version: 1
headspace: neighbors
triggers: ["who is home", "neighbors", "mesh", "who's around", "peer"]
tools: ["announce_presence", "list_neighbors", "mesh_status"]
peers: []
status: active
source: builtin
---

# Local mesh presence

1. Call `announce_presence` if this device has not announced recently.
2. Then `list_neighbors` (scope local or all) or `mesh_status`.
3. Use `describe_neighbor` when the user names a specific peer.
