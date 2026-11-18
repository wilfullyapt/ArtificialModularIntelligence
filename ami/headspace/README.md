# Headspace primitives, tools, and the Brain loop

## What exists today (code truth)

```
Primitive          — name, filespace, settings (no tools)
   └─ Headspace    — @ami_tool methods → TAO agent loop (query)
   └─ BaseWidget   — GUI
   └─ Blueprint    — Flask routes

Brain
  1. select_entry_headspace (corespace prefer / auto router)
  2. prepare_hub → every headspace can list_peer + delegate_to
  3. headspace.query(prompt)  # tools include inherited + delegate
  4. summarize(steps) via personality (corespace-owned voice)
```

## Tool inheritance

`@ami_tool` methods are collected via **MRO** (`collect_tool_methods`), so a
shared primitive/mixin Headspace parent contributes tools to children
(hierarchy / menu of capabilities).

Base Headspace always offers (when a hub is bound):

- `list_peer_headspaces`
- `delegate_to_headspace(name, task)`

## Delegation graph

`DelegationHub` registers all Brain headspaces each turn.

- **Self-referential**: any headspace may delegate to any other.
- **Depth max**: `routing.max_delegate_depth` (default 3) stops A→B→A loops.
- Nested self-delegate at depth>0 is refused.

## Corespace as entry + personality

Config:

```yaml
routing:
  entry: corespace_prefer   # corespace | corespace_first | auto
  max_delegate_depth: 3
```

- Entry hop prefers **corespace** (can answer or delegate).
- Final spoken line is always `Brain.summarize` with personality from
  `~/.ami/personality.prompt` or `~/.ami/data/corespace/personality.prompt`.

Domain headspaces do the work; corespace personality frames how the human hears it.

## Not yet

- GUI menu tree mirroring tool MRO
- Streaming partial delegate observations to the glass
- Typed capability tags beyond tool names
