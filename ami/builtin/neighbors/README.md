# Neighbors Headspace

Local **AMI mesh** discovery plus optional **internet neighbors** (subscription or self-hosted Stronghold directory).

## Tools

- `list_neighbors(scope=local|internet|all)`
- `announce_presence()`
- `mesh_status()`
- `describe_neighbor(name_or_id)`
- `set_neighbor_display_name(display_name)`

## Enable

Add `neighbors` to `enabled_headspaces` in `~/.ami/ami_config.yaml` (from `config_template.yaml`).

## Design

- Local fabric is transport-injectable (`InMemoryMeshBus` default for tests/dev).
- Internet directory disabled until `internet_directory_url` is set; token from env `AMI_NEIGHBORS_TOKEN` by default.
- Peer records persist under the headspace filespace (`peers.json`).

See shipyard ADR 0011 and map `ami-product-triad.md`.
