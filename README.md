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
python -m ami.cli plugin install user/repo@v1.0.0 --enable
python -m ami.cli plugin validate ./my-plugin
python -m ami.cli release install v0.2.0
python -m ami.cli release activate v0.2.0
python -m ami.cli release rollback
python -m ami.cli run
```

Config SoR: `~/.ami/ami_config.yaml` → `enabled_headspaces: [ … ]`  
Data: `~/.ami/data/<headspace>/` · Plugins: `~/.ami/plugins/` · Releases: `~/.ami/releases/` · Receipts: `~/.ami/conversations/`

### C binary CLI (`make cli`)

Optional launcher under `cli/`. Plugin list/enable/disable delegates to `python -m ami.cli`. Prefer the Python CLI for install/release.

## Third-party headspaces

1. Prefer `python -m ami.cli plugin install <user/repo|url|path>@<tag> [--enable]`
2. Or place a package under `~/.ami/plugins/<id>/` with `plugin.toml` (see `docs/plugin.toml.example`) + `__init__.py` exporting `Headspace`
3. Registry still expects a **git tag** on third-party dirs (install creates one)
4. Restart AMI after enable

## Layout

```text
~/.ami/
  ami_config.yaml
  plugins/                 # third-party headspaces
  releases/                # CURRENT, PREVIOUS, <tag>/
  data/<headspace>/        # filespace + skills/
  conversations/           # turn receipts
ami/
  builtin/                 # corespace, markdown, neighbors, …
  builtin/old/             # attic — not loaded
  lifecycle/               # plugin contract, install, release plane
  headspace/               # Primitive, hub, skills
  ai/                      # Brain, Listener, speak
  cli.py                   # operator CLI
```

## First boot

Operator map: **[docs/SETUP.md](docs/SETUP.md)** (setup → install → initial run).

## Roadmap (active)

See **`docs/APPLIANCE_SPINE.md`**: hygiene → plugin/release lifecycle with rollback → cheaper agent path → Pi appliance → **ecosystem** (headspace template, Stronghold directory, mobile mesh).

- Plugin authoring: `docs/HEADSPACE_PLUGIN.md` · template `templates/headspace/` · public `wilfullyapt/ami-headspace-template`
- Neighbors contract: `docs/NEIGHBORS_CONTRACT.md`
- Directory host: `python -m ami.cli directory serve`

## Inspired by

e/acc community · MagicMirror2 · Obsidian (files > app)
