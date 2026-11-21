# Headspace primitives, tools, peers, skills, and the Brain loop

## What exists today (code truth)

```
Primitive          — name, filespace, settings, skills_dir
   └─ Headspace    — @ami_tool + skills inject → TAO agent loop
   └─ BaseWidget   — GUI
   └─ Blueprint    — Flask routes

Brain
  1. start TurnReceipt (session + human text)
  2. prepare_hub(turn) → peers: list / ask / do / call_tool
  3. select_entry_headspace (corespace prefer / auto router)
  4. headspace.query(prompt)  # tools + matched skills + peers
  5. summarize(steps) via personality
  6. finish+persist turn JSON; log route_summary
  7. if ask/do/skill/tool hops → draft skill under entry skills/drafts/
```

## Tools vs skills

| | Tools | Skills |
|---|---|---|
| Where | Python `@ami_tool` in git | `~/.ami/data/<hs>/skills/*.md` |
| Change | code release | edit / promote draft |
| Role | deterministic acts | procedures the LLM follows |

Builtin defaults ship in `ami/builtin/<hs>/skills/` and **copy once** into filespace (never overwrite user edits).

## Base Headspace peer surface

| Tool | Cost | Use when |
|---|---|---|
| `list_peer_headspaces` | free | discover peers |
| `list_headspace_tools` | free | discover domain tools |
| `call_headspace_tool(hs, tool, args_json)` | **1 step, no nested agent** | known tool + args |
| `ask_headspace` | full peer agent | open info questions |
| `do_headspace` | full peer agent | peer must multi-step reason |
| `delegate_to_headspace` | alias of do | legacy |

Skills: `list_skills`, `promote_skill_draft` (never auto-promote).

Direct RPC refuses peer meta-tools (ask/do/call/…) to stop re-entrancy.

## Receipts

`TurnReceipt` under `~/.ami/conversations/<session>/turns/`.  
Route example: `corespace → tool:markdown.ping → speak`

## Skills (P2)

`filespace/skills/*.md` + `drafts/`. Trigger match injects into query.

## Config

```yaml
routing:
  entry: corespace_prefer
  max_delegate_depth: 3
  max_steps: 24
```

## Not yet

- GUI tree view of turn receipts / skill browser
- Failure-linked pitfall auto-append
- Streaming partial peer observations to the glass
- Native provider tool-calling (still JSON-TAO agent)
