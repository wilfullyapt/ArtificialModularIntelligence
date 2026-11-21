# Headspace primitives, tools, peers, and the Brain loop

## What exists today (code truth)

```
Primitive          — name, filespace, settings
   └─ Headspace    — @ami_tool methods → TAO agent loop (query)
   └─ BaseWidget   — GUI
   └─ Blueprint    — Flask routes

Brain
  1. start TurnReceipt (session + human text)
  2. prepare_hub(turn) → every headspace can list_peer + ask/do
  3. select_entry_headspace (corespace prefer / auto router)
  4. headspace.query(prompt)  # tools include inherited + peers
  5. summarize(steps) via personality
  6. finish+persist turn JSON; log route_summary
```

## Tool inheritance

`@ami_tool` methods are collected via **MRO** (`collect_tool_methods`), so a
shared primitive/mixin Headspace parent contributes tools to children
(hierarchy / menu of capabilities).

Base Headspace always offers (when a hub is bound):

- `list_peer_headspaces`
- `ask_headspace(name, question)` — info hop
- `do_headspace(name, task)` — action hop
- `delegate_to_headspace` — legacy alias of do

## Delegation graph + receipts (P0/P1)

`DelegationHub` registers all Brain headspaces each turn.

- **Self-referential**: any headspace may ask/do any other.
- **Depth max**: `routing.max_delegate_depth` (default 3).
- **Step budget**: `routing.max_steps` (default 24) shared across the turn.
- **PeerResult**: structured ok/observation/span_ids from ask/do.
- **TurnReceipt**: span tree under `~/.ami/conversations/<session>/turns/<turn>.json`
  with `route_summary` like `corespace → ask:neighbors → do:markdown → speak`.

## Corespace as entry + personality

Config:

```yaml
routing:
  entry: corespace_prefer   # corespace | corespace_first | auto
  max_delegate_depth: 3
  max_steps: 24
```

- Entry hop prefers **corespace** (can answer or ask/do peers).
- Final spoken line is always `Brain.summarize` with personality from
  `~/.ami/personality.prompt` or `~/.ami/data/corespace/personality.prompt`.

Domain headspaces do the work; corespace personality frames how the human hears it.

## Not yet (P2+)

- Per-headspace `filespace/skills/*.md` loader + self-improve drafts
- Direct tool RPC (`call_headspace_tool`) without nested agent
- GUI tree view of turn receipts
- Streaming partial peer observations to the glass
