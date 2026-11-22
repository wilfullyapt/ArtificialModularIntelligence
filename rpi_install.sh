#!/usr/bin/env bash
# AMI kiosk installer — safe / idempotent (P0 day-zero)
# Does NOT delete ~/.ami. Does NOT rm -rf an existing checkout.
set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  echo "Error: run with bash" >&2
  exit 1
fi

AMI_REPO_URL="${AMI_REPO_URL:-https://github.com/wilfullyapt/ArtificialModularIntelligence.git}"
AMI_REPO_DIR="${AMI_REPO_DIR:-$HOME/ArtificialModularIntelligence}"
# Default craft tip; override with AMI_BRANCH=prod for product tip
AMI_BRANCH="${AMI_BRANCH:-feat/appliance-spine}"
AMI_SKIP_APT="${AMI_SKIP_APT:-0}"
AMI_WITH_STT="${AMI_WITH_STT:-1}"
AMI_INSTALL_SYSTEMD="${AMI_INSTALL_SYSTEMD:-1}"
AMI_REQUIRE_PI="${AMI_REQUIRE_PI:-1}"

log() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

if [ "$AMI_REQUIRE_PI" = "1" ]; then
  if ! grep -qi "Raspberry Pi" /proc/cpuinfo 2>/dev/null \
    && ! grep -qi "Raspberry Pi" /sys/firmware/devicetree/base/model 2>/dev/null; then
    die "This installer defaults to Raspberry Pi. Set AMI_REQUIRE_PI=0 for other Linux kiosks."
  fi
fi

if ! echo "${PATH:-}" | grep -q "$HOME/.local/bin"; then
  mkdir -p "$HOME/.local/bin"
  if [ -f "$HOME/.bashrc" ] && ! grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    log "Added ~/.local/bin to PATH in ~/.bashrc"
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ "$AMI_SKIP_APT" != "1" ]; then
  log "Updating apt and installing build deps..."
  sudo apt update
  sudo apt install -y \
    build-essential git curl \
    python3 python3-dev python3-pip python3-venv \
    portaudio19-dev libasound2-dev \
    libgl1 libxkbcommon0 libegl1 \
    || log "apt partially failed — continuing if python/git already present"
fi

if ! command -v uv >/dev/null 2>&1; then
  log "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # shellcheck disable=SC1090
  [ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env" || true
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || die "uv not on PATH after install"

if [ -d "$AMI_REPO_DIR/.git" ]; then
  log "Existing checkout: $AMI_REPO_DIR (fetch + checkout $AMI_BRANCH)"
  git -C "$AMI_REPO_DIR" remote set-url origin "$AMI_REPO_URL" 2>/dev/null || true
  git -C "$AMI_REPO_DIR" fetch origin
  git -C "$AMI_REPO_DIR" checkout "$AMI_BRANCH"
  git -C "$AMI_REPO_DIR" pull --ff-only origin "$AMI_BRANCH" \
    || log "ff-only pull skipped (local commits or diverged) — leaving tree on $AMI_BRANCH"
elif [ -e "$AMI_REPO_DIR" ]; then
  die "AMI_REPO_DIR exists but is not a git repo: $AMI_REPO_DIR (move it or set AMI_REPO_DIR)"
else
  log "Cloning $AMI_REPO_URL ($AMI_BRANCH) → $AMI_REPO_DIR"
  if ! git clone --branch "$AMI_BRANCH" --single-branch "$AMI_REPO_URL" "$AMI_REPO_DIR"; then
    git clone "$AMI_REPO_URL" "$AMI_REPO_DIR"
    git -C "$AMI_REPO_DIR" checkout "$AMI_BRANCH"
  fi
fi

cd "$AMI_REPO_DIR"

log "Syncing Python env (uv)..."
uv sync
if [ "$AMI_WITH_STT" = "1" ]; then
  log "Installing [stt]/[pi] extras (faster-whisper)..."
  uv pip install -e ".[pi]" || uv pip install -e ".[stt]" || log "STT extra install failed — install later"
fi

log "Day-zero init (config + secrets scaffold; never wipes existing)..."
uv run python -m ami.cli init

LAUNCHER="$HOME/.local/bin/ami"
cat > "$LAUNCHER" << EOF
#!/usr/bin/env bash
# AMI launcher — prefers checkout venv
set -euo pipefail
REPO="${AMI_REPO_DIR}"
if [ -x "\$REPO/.venv/bin/python" ]; then
  exec "\$REPO/.venv/bin/python" -m ami.cli "\$@"
fi
exec python3 -m ami.cli "\$@"
EOF
chmod +x "$LAUNCHER"
log "Launcher: $LAUNCHER"

if [ "$AMI_INSTALL_SYSTEMD" = "1" ]; then
  log "Installing user systemd unit..."
  uv run python -m ami.cli systemd install \
    --repo-dir "$AMI_REPO_DIR" \
    --display "${DISPLAY:-:0}" || log "systemd install failed — run: ami systemd install"
  systemctl --user daemon-reload 2>/dev/null || true
  log "Enable on boot (after graphical login): systemctl --user enable --now ami.service"
  log "Optional linger: sudo loginctl enable-linger \"\$USER\""
fi

log ""
log "=== AMI install complete ==="
log "  repo:    $AMI_REPO_DIR @ $AMI_BRANCH"
log "  config:  ~/.ami/ami_config.yaml"
log "  secrets: ~/.ami/.env  (edit keys; never commit)"
log "  doctor:  ami doctor"
log "  run:     ami run"
log "  audio:   I2S HAT-style custom PCB (ALSA default until board lands)"
log "  ~/.ami was NOT deleted."
