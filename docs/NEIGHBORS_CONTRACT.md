# Neighbors contract (frozen v1)

**Status:** Phase E SoR — shared by AMI, mobile-ami, Stronghold directory  
**Magic:** `AMI-MESH1` · **UDP default port:** `4177` · **Directory default port:** `4178`

## Peer JSON

```json
{
  "peer_id": "opaque-device-id",
  "display_name": "Kitchen AMI",
  "kind": "local|internet",
  "endpoint": "ami-mesh://… or https://…",
  "capabilities": ["mesh", "voice"],
  "last_seen": 1730000000.0
}
```

Rules:

- `peer_id` opaque string (device-generated); display names human-editable
- Directory responses force `kind=internet`
- LAN mesh beacons use the same fields inside `AMI-MESH1` JSON (plus `magic`, `ts`)
- Do **not** fork this schema on mobile-ami

## LAN beacon (`AMI-MESH1`)

```json
{
  "magic": "AMI-MESH1",
  "peer_id": "…",
  "display_name": "…",
  "endpoint": "…",
  "capabilities": ["mesh"],
  "ts": 1730000000.0
}
```

UDP broadcast/unicast on port **4177**.

## Directory HTTP API v1

Base URL example: `http://stronghold:4178`

| Method | Path | Auth | Body / response |
|--------|------|------|-----------------|
| GET | `/health` | none | `{ok, service}` |
| GET | `/v1/neighbors` | Bearer if token set | `{api_version:"1", peers:[…]}` |
| POST | `/v1/neighbors` | Bearer if token set | peer JSON → `{ok, peer}` |
| DELETE | `/v1/neighbors/{peer_id}` | Bearer if token set | `{ok, peer_id}` |

Auth header: `Authorization: Bearer <token>` (env `AMI_NEIGHBORS_TOKEN` on clients).

TTL: server may drop peers with `last_seen` older than configured TTL (default 3600s).

## Client settings (AMI Neighbors headspace)

- `internet_directory_url` — base URL
- `internet_directory_token_env` — default `AMI_NEIGHBORS_TOKEN`
- `mesh_transport`: `memory` or `udp`
- `mesh_port`: `4177`

## Run directory (Stronghold)

```bash
python -m ami.neighbors_directory --host 0.0.0.0 --port 4178 \
  --data ~/.ami/directory/peers.json --token "$AMI_NEIGHBORS_TOKEN"
# or
python -m ami.cli directory serve --host 0.0.0.0 --port 4178
```

Lamassu owns production host deploy; this module is the craft binary + contract.
