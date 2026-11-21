# Appliance spine plan

**Branch:** `feat/appliance-spine` (cut from `prod` after PR #4 squash)  
**Goal:** Keep Headspace product model; industrialize lifecycle (CLI, plugins, update/rollback).

## Phase A — Truth & hygiene (this branch, in progress)

- [x] Quarantine `ami/builtin/old` from PluginRegistry discovery
- [x] Python operator CLI matching `enabled_headspaces` list (`ami.cli`)
- [x] README rewritten to code truth
- [x] IPC README: mark unused priority/command-queue as non-SoR
- [x] C `ami run` launches `python -m ami.main` (not missing ami.py)
- [x] C plugin commands delegate to `python -m ami.cli` where possible
- [x] Orphan `tests/cli/test_python_cli.py` replaced by unit tests for `ami.cli`

## Phase B — Operator spine

- Plugin contract (`plugin.toml` / validate on install)
- `ami plugin install <git-url>@<tag>`
- Release plane: `releases/<tag>`, activate, **rollback**
- `ami doctor` expanded (smoke import + last receipt)

## Phase C — Cognition cost

- Native tool-calling adapters; TAO fallback
- Enforce call_tool-first peer path

## Phase D — Pi appliance

- Flask worker slim; STT extras; receipt debug view

## Phase E — Ecosystem

- Public headspace template; Stronghold directory; mobile-ami mesh client
