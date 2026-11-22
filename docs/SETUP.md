# AMI — Initial setup, install, and first run

**Branch tip this map tracks:** `feat/appliance-spine` (craft) · product tip `prod`  
**Product posture:** **Standalone primary kiosk** (glass + voice). Not headless-desk; Stronghold/Reliquary optional.  
**No PR required** — operator map only.  
**Backlog:** day-0 installer/systemd/secrets + custom 2-speaker+mic PCB (shipyard backlog 2026-11-21).  
**Related:** `docs/APPLIANCE_SPINE.md` (A–E craft roadmap) · `ASSEMBLY.md` (hardware BOM) · `README.md`

---

## 0. What you are bringing up

AMI is a **three-process appliance**:

1. **AI** — wake/STT → Brain → Headspace tools → speak  
2. **BACKEND** — Flask/Gunicorn (blueprints, settings, `/receipts`)  
3. **GUI** — PyQt6 MainWindow + Headspace widgets  

IPC ties them together. Data always lives under **`~/.ami/`**, not only in the git tree.

**Python pin:** `>=3.11,<3.12`  
**Package manager (preferred):** `uv`  
**OS for full glass:** Linux + display (Pi OS Desktop for on-device PyQt; Lite needs remote/display story)

---

## 1. Paths (SoR)

| Path | Role |
|------|------|
| Repo checkout | Code + `config_template.yaml` |
| `~/.ami/` | Device home (created on first Config load) |
| `~/.ami/ami_config.yaml` | **Config SoR** (copied from template if missing) |
| `~/.ami/.env` | Secrets (API keys) — never commit |
| `~/.ami/plugins/` | Third-party headspaces |
| `~/.ami/releases/` | Side-by-side core tags + `CURRENT`/`PREVIOUS` |
| `~/.ami/data/<hs>/` | Per-headspace filespace + skills |
| `~/.ami/conversations/` | Turn receipts |
| `~/.ami/directory/` | Optional peers JSON if directory `--data` set |

First Config construction **auto-copies** `config_template.yaml` → `~/.ami/ami_config.yaml` if absent.

---

## 2. Hardware baseline (from ASSEMBLY.md)

**Minimum kiosk bring-up**

- Pi 5 (or strong x86 Linux desk for dev)  
- HDMI monitor (GUI)  
- USB speakerphone **or** working mic+speakers  
- Network (Ethernet preferred for Neighbors LAN)  
- Optional: AI HAT, Ollama on-box or LAN, UPS  

**Not required for first software boot:** Hailo, paid subscription, internet neighbors directory.

Open Wil decisions still on ASSEMBLY (glass type, default audio, default `llm.backend`, HAT in standard kit vs addon).

---

## 3. Install paths (pick one)

### A. Dev workstation (checkout)

```bash
git clone https://github.com/wilfullyapt/ArtificialModularIntelligence.git
cd ArtificialModularIntelligence
# Prefer craft tip while vibe-branching:
# git fetch && git checkout feat/appliance-spine

# Python 3.11
uv sync
# heavier: GUI/audio already in main deps; local whisper:
# uv pip install '.[stt]'   # or pip install -e '.[stt]'

# Optional C launcher into ~/.local/bin/ami
make cli
# Full make install = cli + uv sync
make install
```

**Headless sanity (no display/mic):**

```bash
PYTHONPATH=. pytest tests/unit/test_phase_e.py tests/unit/neighbors -q
# or CI-shaped suite via .github/workflows/headless.yml
python -m ami.cli doctor
```

### B. Raspberry Pi first boot script

`rpi_install.sh` (must run **on Pi**, with sudo):

1. apt: build-essential, python3, venv, git  
2. install `uv` if missing  
3. clone `AMI_REPO_URL` (default official origin) into `AMI_REPO_DIR`  
4. `make install`  
5. claims you can run `ami`  

**Gaps / honesty**

- Script **deletes** existing `AMI_REPO_DIR` then reclones — destructive  
- Does **not** pin branch (`prod` vs `feat/appliance-spine`)  
- Does **not** install `.[stt]` / Ollama / systemd unit  
- Console script name `ami` from pyproject points at `ami.main:main` **after** package install; `make cli` installs **C** binary also named `ami` — prefer one story (Python `python -m ami.cli` / `python -m ami.main` is clearest)

Env overrides:

- `AMI_REPO_URL`  
- `AMI_REPO_DIR`  

### C. Appliance release plane (post-install updates)

```bash
python -m ami.cli release install <tag>
python -m ami.cli release activate <tag>
python -m ami.cli run --release          # or AMI_USE_RELEASE=1
python -m ami.cli release rollback
```

Dev checkout run stays default (`run` without `--release`).

---

## 3b. Day-zero commands (P0)

```bash
ami init                 # ~/.ami + config + .env scaffold
ami secrets check        # presence only — never prints values
ami doctor
ami systemd install      # user unit → ami run
systemctl --user enable --now ami.service
ami run                  # foreground full glass appliance
```

Installer: `bash rpi_install.sh` (idempotent; `AMI_BRANCH` pin; **does not** delete `~/.ami`).

Audio target: **I2S HAT-style** custom PCB (2 spk + mic). Interim USB OK for software bring-up.
PCB brief: `docs/hardware/PCB_BRIEF_I2S_AUDIO.md`.

## 4. Initial configuration

### 4.1 Generate config

Any of:

```bash
python -m ami.cli doctor          # constructs Config → copies template if needed
# or first full run
```

Edit: `~/.ami/ami_config.yaml`

### 4.2 Minimum knobs for a useful first run

**Identity / locale**

- `timezone`  

**LLM (pick one path)**

```yaml
llm:
  backend: ollama          # or xai | anthropic
  model: llama3.2:1b
  ollama_base_url: http://127.0.0.1:11434/v1
  agent: auto              # native tools if backend supports chat_with_tools
```

- Local: install/run **Ollama**, pull model  
- Cloud: put keys in `~/.ami/.env` (provider-specific; do not commit)

**STT**

```yaml
stt:
  backend: local           # needs faster-whisper extra
  model: tiny
  device: cpu
# or legacy: backend: google
```

Install whisper path: `pip/uv install 'ArtificialModularIntelligence[stt]'` from checkout.

**Headspaces (list SoR — not true/false map)**

```yaml
enabled_headspaces:
  - corespace
  - markdown
  - neighbors
```

**Audio / wake**

- `hot_word`, `detection_threshold`, `listening_patience`, `listening_timeout`  
- USB mic must be default capture device for openWakeWord path  

**Server (kiosk defaults already in template)**

```yaml
host: 0.0.0.0
port: 5000
server:
  workers: 1
  threads: 2
  kill_ami_on_exit: false
```

**Neighbors (optional day-one)**

```yaml
neighbors:
  mesh_port: 4177
  # internet_directory_url: http://stronghold:4178
```

Token for directory: env `AMI_NEIGHBORS_TOKEN`.

**Routing / speak**

```yaml
routing:
  entry: corespace_prefer
  max_delegate_depth: 3
  max_steps: 24
  speak: auto
```

### 4.3 Verify config surface

```bash
python -m ami.cli doctor
python -m ami.cli plugin list
```

Doctor reports: config path, data dir, plugins, releases, enabled list, llm/stt/speak, last receipt if any.

---

## 5. Initial running

### 5.1 Full appliance (production-shaped)

```bash
# from checkout with deps installed
python -m ami.main
# or package console / C wrapper once installed:
# ami
# operator wrapper:
python -m ami.cli run
python -m ami.cli run --release    # activated CURRENT only
```

Starts **AI + Flask + GUI** together. Needs display for GUI process.

**HTTP after up**

- Flask host/port from config (default `0.0.0.0:5000`)  
- Receipt browser (spine D): `/receipts`, `/api/receipts`  

### 5.2 Dev partial processes (desk debug)

```bash
make dev
make dev ARGS='--ai --gui'
make dev ARGS='--ai --server --debug'
make idev ARGS='--ai --debug'    # interactive Python + selected processes
# equivalent:
uv run python -m ami.dev --ai --server --debug
```

Flags: `--ai` `--gui` `--server` `--debug`  
If **any** process flag is passed, only those run; if **none**, all three default on (see `ami/dev.py` parse rules).

### 5.3 Day-one functional checklist

1. `doctor` clean (config exists, enabled headspaces non-empty)  
2. GUI window appears (or intentional headless: AI+server only)  
3. Flask responds on configured port  
4. Wake word or push-to-talk path produces a turn (mic working)  
5. Receipt JSON under `~/.ami/conversations/…/turns/`  
6. Optional: `neighbors` tools list/announce on LAN  
7. Optional: second box sees peer after both announce  

### 5.4 Ecosystem add-ons (not required for first glass)

```bash
# third-party headspace
python -m ami.cli plugin install wilfullyapt/ami-headspace-template@v0.1.0 --enable

# household internet directory (Stronghold host; Lamassu ops for prod)
python -m ami.cli directory serve --host 0.0.0.0 --port 4178 \
  --data ~/.ami/directory/peers.json
# point clients: internet_directory_url + AMI_NEIGHBORS_TOKEN
```

---

## 6. Recommended bring-up order (operator)

| Step | Action | Done when |
|------|--------|-----------|
| 1 | Hardware seat + OS + network | SSH + HDMI + audio device visible |
| 2 | Clone + `uv sync` / `make install` | `python -m ami.cli doctor` runs |
| 3 | First config materialize + edit llm/stt | YAML matches chosen brain path |
| 4 | Ollama up **or** cloud `.env` keys | One successful LLM chat outside AMI optional |
| 5 | `.[stt]` if local STT | import/faster-whisper available |
| 6 | `python -m ami.cli run` or `make dev` | Three processes (or chosen subset) alive |
| 7 | One spoken or injected turn | Receipt on disk |
| 8 | Enable/tune neighbors | Optional LAN peer |
| 9 | systemd user/system unit | Autostart on boot (not shipped yet — gap) |
| 10 | `release install/activate` | Only after a tagged appliance build exists |

---

## 7. Known gaps (map honestly — fix later, not pretend)

1. **No first-class systemd unit** in-repo for `ami.main`  
2. **`rpi_install.sh`** destructive reclone; no branch pin; no Ollama/STT/systemd  
3. **Dual `ami` entry ambiguity** (pyproject script vs C `make cli` binary)  
4. **Full `pip install -e .`** pulls PortAudio/PyQt — desk without mic/display is painful; headless tests use minimal deps  
5. **ASSEMBLY** still draft on glass/audio/default llm/HAT SKU  
6. **Prod vs craft tip:** appliance-spine features (directory serve, template docs, run --release polish) live on **feat tip** until you merge; `prod` is PR #4 cognition/neighbors stack  

---

## 8. Quick command card

```bash
# install
uv sync && make cli                     # or: bash rpi_install.sh on Pi

# configure
python -m ami.cli doctor
$EDITOR ~/.ami/ami_config.yaml
# optional secrets:
$EDITOR ~/.ami/.env

# run
python -m ami.cli run                   # full appliance from checkout
make dev ARGS='--ai --server --debug' # partial
python -m ami.cli run --release         # CURRENT release tree only

# inspect
python -m ami.cli plugin list
python -m ami.cli release status
# browser: http://<host>:5000/receipts
```

---

## 9. Usage roadmap (how this map sits)

| Layer | Doc / SoR | Status |
|-------|-----------|--------|
| Product nouns | Reliquary `ami-product-triad`, ADR 0010/0011 | Locked |
| Craft spine | `docs/APPLIANCE_SPINE.md` Phases A–E | Done on feat tip |
| Hardware | `ASSEMBLY.md` | Draft BOM + open Wil checks |
| **Operator day-0** | **This file** | Mapped; install gaps listed |
| Ecosystem | template repo, directory server, mobile mesh | Code ready; ops deploy optional |
| Merge to prod | Your call — no PR until asked | Waiting |

Next craft after this map (when you order it): tighten **install path** (non-destructive Pi script, branch pin, systemd unit, single `ami` launcher story) against this checklist — still no PR until you say so.
