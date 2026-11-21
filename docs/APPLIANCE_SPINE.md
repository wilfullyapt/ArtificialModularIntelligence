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

- [x] Native tool-calling agent (`NativeToolAgent`) via `chat_with_tools` on Ollama/xAI
- [x] Factory `llm.agent: auto|native|tao` (default auto)
- [x] TAO fallback + call_tool-first peer guidance in system prompts/skills
- [x] Fixed TAO `custom_tool_call` wiring; removed debug `print(steps)`

## Phase D — Pi appliance

- [x] Flask/Gunicorn kiosk defaults (`server.workers=1`, `threads=2`); exit no longer kills AMI by default
- [x] Receipt browser: `/receipts`, `/receipts/<session>/<turn>`, `/api/receipts`
- [x] Optional deps: `[stt]` / `[pi]` extras for faster-whisper
- [x] `ami.cli run --release` (or `AMI_USE_RELEASE=1`) prefers `~/.ami/releases/CURRENT`

## Phase E — Ecosystem

- [x] Freeze peer + directory contract (`docs/NEIGHBORS_CONTRACT.md`)
- [x] Public headspace template in-tree (`templates/headspace`) + author doc
- [x] Stronghold directory server (`python -m ami.neighbors_directory`) + live HTTP client
- [x] CLI: `ami.cli directory serve`
- [x] mobile-ami mesh client (parity package + tests on handheld tip)
- [x] Public GitHub mirror of template (`wilfullyapt/ami-headspace-template`)

## Operator cheatsheet

```bash
python -m ami.cli plugin validate ./path/to/plugin
python -m ami.cli plugin install user/repo@v0.1.0 --enable
python -m ami.cli plugin install wilfullyapt/ami-headspace-template@v0.1.0 --enable
python -m ami.cli release install v0.2.0
python -m ami.cli release activate v0.2.0
python -m ami.cli release rollback
python -m ami.cli directory serve --host 0.0.0.0 --port 4178
python -m ami.neighbors_directory --data ~/.ami/directory/peers.json
python -m ami.cli run              # dev checkout
python -m ami.cli run --release    # activated CURRENT tree
python -m ami.cli doctor
# pip install 'ArtificialModularIntelligence[stt]'  # local whisper on Pi
```

Releases live under `~/.ami/releases/`. Plugins under `~/.ami/plugins/<id>/`.
Directory peers under `~/.ami/directory/` when `--data` is set. Contract: `docs/NEIGHBORS_CONTRACT.md`.
