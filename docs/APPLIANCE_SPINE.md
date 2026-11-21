# Appliance spine plan

**Branch:** `feat/appliance-spine` (cut from `prod` after PR #4 squash)  
**Goal:** Keep Headspace product model; industrialize lifecycle (CLI, plugins, update/rollback).

## Phase A — Truth & hygiene

- [x] Quarantine `ami/builtin/old` from PluginRegistry discovery
- [x] Python operator CLI matching `enabled_headspaces` list (`ami.cli`)
- [x] README rewritten to code truth
- [x] IPC README: mark unused priority/command-queue as non-SoR
- [x] C `ami run` launches `python -m ami.main` (not missing ami.py)
- [x] C plugin commands delegate to `python -m ami.cli` where possible
- [x] Orphan `tests/cli/test_python_cli.py` replaced by unit tests for `ami.cli`

## Phase B — Operator spine

- [x] Plugin contract (`plugin.toml` + `__init__` AST checks)
- [x] `ami plugin install <git-url|user/repo|path>@tag` + `validate`
- [x] Release plane: `~/.ami/releases/<tag>`, `CURRENT`/`PREVIOUS`, activate, **rollback**, smoke import
- [x] `ami doctor` expanded (releases + last turn + import smoke)
- [x] Example `docs/plugin.toml.example`

## Phase C — Cognition cost

- Native tool-calling adapters; TAO fallback
- Enforce call_tool-first peer path

## Phase D — Pi appliance

- Flask worker slim; STT extras; receipt debug view
- Optionally bind `run` to activated `CURRENT` release tree

## Phase E — Ecosystem

- Public headspace template; Stronghold directory; mobile-ami mesh client

## Operator cheatsheet

```bash
python -m ami.cli plugin validate ./path/to/plugin
python -m ami.cli plugin install user/repo@v1.0.0 --enable
python -m ami.cli release install v0.2.0
python -m ami.cli release activate v0.2.0
python -m ami.cli release rollback
python -m ami.cli doctor
```

Releases live under `~/.ami/releases/`. Plugins under `~/.ami/plugins/<id>/`.
