# Headspace primitives, tools, peers, skills, and the Brain loop

## What exists today (code truth)

```
Primitive          — name, filespace, settings, skills_dir
   └─ Headspace    — @ami_tool + skills inject → TAO agent loop
   └─ BaseWidget   — GUI
   └─ Blueprint    — Flask routes

Brain
  1. start TurnReceipt (session + human text)
  2. prepare_hub(turn) → every headspace can list_peer + ask/do
  3. select_entry_headspace (corespace prefer / auto router)
  4. headspace.query(prompt)  # tools + matched skills + peers
  5. summarize(steps) via personality
  6. finish+persist turn JSON; log route_summary
  7. if ask/do/skill hops → draft skill under entry filespace/skills/drafts/
```

## Tools vs skills

| | Tools | Skills |
|---|---|---|
| Where | Python `@ami_tool` in git | `~/.ami/data/<hs>/skills/*.md` |
| Change | code release | edit / promote draft |
| Role | deterministic acts | procedures the LLM follows |

Builtin defaults ship in `ami/builtin/<hs>/skills/` and **copy once** into filespace (never overwrite user edits).

## Base Headspace tools

Peers:

- `list_peer_headspaces`
- `ask_headspace` / `do_headspace` / `delegate_to_headspace` (alias)

Skills:

- `list_skills`
- `promote_skill_draft` (human confirm — never auto-promote)

## Delegation + receipts (P0/P1)

`DelegationHub` ask/do + `TurnReceipt` spans under conversations/. See prior notes.

## Skills (P2)

```text
~/.ami/data/<headspace>/skills/
  grocery-list-house.md     # active
  drafts/
    from-turn-abc.md        # draft only until promote
```

Frontmatter: `id`, `version`, `triggers`, `tools`, `status` (active|draft|retired), `source`.

`Headspace.query` injects matching active skills into the prompt and records `skill` spans on the turn.

## Config

```yaml
routing:
  entry: corespace_prefer
  max_delegate_depth: 3
  max_steps: 24
```

## Not yet (P3+)

- Direct tool RPC (`call_headspace_tool`) without nested agent
- GUI tree view of turn receipts / skill browser
- Failure-linked pitfall auto-append
- Streaming partial peer observations to the glass
