# Artificial Modular Intelligence

**AMI** is an in-home AI companion (typically Raspberry Pi + monitor) built around **Headspaces**: modular plugins that can provide LLM tools, a PyQt glass widget, and/or a Flask blueprint.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What works today (code truth)

| Area | Status |
|------|--------|
| Builtin headspaces | `corespace`, `markdown`, `neighbors` (default enabled); `media`/`company` present |
| Peer routing | `ask_headspace` / `do_headspace` / `call_headspace_tool` + turn receipts |
| Skills | Per-headspace `~/.ami/data/<hs>/skills/` (markdown); draft/promote |
| Speak | `routing.speak: auto\|thin\|llm` (thin avoids a second LLM when possible) |
| Inference | `llm.backend: ollama \| xai \| anthropic` |
| STT | `stt.backend: local` (faster-whisper, optional dep) or `google` |
| Hardware notes | [ASSEMBLY.md](ASSEMBLY.md) |
| CI | `.github/workflows/headless.yml` (unit tests, no GUI/audio) |

**Related products:** [mobile-ami](https://github.com/wilfullyapt/mobile-ami) (handheld); **Stronghold** (household infra / optional neighbor directory). Hermes doorway (narthex) is a separate path.

## Dev quickstart

```bash
git clone https://github.com/wilfullyapt/ArtificialModularIntelligence.git
cd ArtificialModularIntelligence
# Python 3.11
uv sync   # or: pip install -e .  (GUI/audio deps are heavy)

# Headless unit tests
PYTHONPATH=. pytest tests/unit -q

# Full appliance (needs display + mic for real use)
make dev
# optional process subset:
make dev ARGS='--ai --gui'
make idev ARGS='--ai --debug'   # interactive
```

Entry points:

- `python -m ami.main` — full three-process run (AI + Flask + GUI)
- `python -m ami.dev` — dev runner with `--ai/--gui/--server/--debug`
- `python -m ami.cli …` — operator CLI (plugin enable list, doctor, run)

## Operator CLI (Python)

```bash
python -m ami.cli doctor
python -m ami.cli plugin list
python -m ami.cli plugin enable neighbors
python -m ami.cli plugin disable media
python -m ami.cli run
```

Config SoR: `~/.ami/ami_config.yaml` → `enabled_headspaces: [ … ]`  
Data: `~/.ami/data/<headspace>/` · Plugins: `~/.ami/plugins/` · Receipts: `~/.ami/conversations/`

### C binary CLI (`make cli`)

Optional fast launcher under `cli/`. Prefer `python -m ami.cli` for plugin config (matches YAML list).  
`ami update` / `gethead` exist but are **thin sketches** (no release rollback yet — see `docs/APPLIANCE_SPINE.md`).

## Third-party headspaces

1. Place a git checkout under `~/.ami/plugins/<name>` (or `ami gethead user/repo` clone helper).
2. Repo must be a package with `__init__.py` exporting `Headspace` (and optional `GUI`/`Blueprint`), `EXAMPLES`, and a **git tag** (registry uses latest tag as version).
3. `python -m ami.cli plugin enable <name>` then restart AMI.

## Layout

```text
~/.ami/
  ami_config.yaml
  plugins/                 # third-party headspaces
  data/<headspace>/        # filespace + skills/
  conversations/           # turn receipts
ami/
  builtin/                 # corespace, markdown, neighbors, …
  builtin/old/             # attic — not loaded
  headspace/               # Primitive, hub, skills
  ai/                      # Brain, Listener, speak
  cli.py                   # operator CLI
```

## Roadmap (active)

See **`docs/APPLIANCE_SPINE.md`**: hygiene → plugin/release lifecycle with rollback → cheaper agent path → Pi appliance hardening.

## Inspired by

e/acc community · MagicMirror2 · Obsidian (files > app)
