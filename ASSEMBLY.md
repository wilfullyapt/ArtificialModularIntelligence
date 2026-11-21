# AMI Home Appliance — BOM & Assembly

**Status:** Draft form-factor lock (2026-11-18) · vibe branch `feat/neighbors-headspace`  
**Product:** Artificial Modular Intelligence — **home kiosk** companion (Pi + glass/monitor)  
**Related handheld BOM:** see `mobile-ami` `ASSEMBLY.md` (different SKU)

This is the **first written BOM** for desktop/home AMI. Prices are approximate USD street; buy what matches the pin/role notes.

---

## Form factor (locked intent)

| | Home AMI | mobile-ami (not this kit) |
|--|----------|---------------------------|
| Role | Wall/desk kiosk + Headspaces GUI | Pocket offline assistant |
| Display | HDMI monitor / MM-class glass | SH1106 OLED |
| Power | Mains (UPS optional) | 18650 UPS required |
| Default brain | Local Ollama **and/or** cloud | Offline Ollama first |
| Mesh | Neighbors headspace (LAN + optional internet directory) | Parity later |

---

## Bill of Materials (v0 kiosk)

### Core compute

| # | Part | Qty | Notes | ~$ |
|---|------|-----|-------|-----|
| 1 | **Raspberry Pi 5 8GB** | 1 | Primary. Pi 4 8GB acceptable for cloud-only bring-up | 80–125 |
| 2 | **Official active cooler** (Pi 5) or quality heatsink | 1 | Headspaces + optional local LLM need thermal headroom | 10–15 |
| 3 | **microSD 64GB+** (A2) or NVMe via Pi 5 PCIe | 1 | Prefer NVMe if local models stay on-device | 10–80 |
| 4 | **27 W+ USB-C PSU** (Pi 5 official preferred) | 1 | | 12–20 |

### Optional local inference (AI HAT path)

| # | Part | Qty | Notes | ~$ |
|---|------|-----|-------|-----|
| 5 | **Raspberry Pi AI HAT+ (Hailo-8 or Hailo-10H class)** | 0–1 | **Optional.** Enables accelerated local STT/LLM paths later. Not required for cloud inference or Neighbors mesh | 70–130 |
| 6 | PCIe FFC ribbon (if not bundled) | 0–1 | HAT uses PCIe — no 40-pin conflict with HATs that need GPIO | incl. |

Omit row 5–6 for **cloud-only** or **CPU Ollama** desks. Software must boot either way.

### Audio I/O

| # | Part | Qty | Notes | ~$ |
|---|------|-----|-------|-----|
| 7 | **USB speakerphone** *or* ReSpeaker / I2S mic HAT + powered speakers | 1 | v0 recommends **USB speakerphone** for simplest bring-up (no I2S driver fight). ReSpeaker path can share mobile-ami lessons later | 30–80 |
| 8 | 3.5 mm / HDMI audio as fallback | — | Prefer one dedicated capture device for openWakeWord | — |

### Display / human glass

| # | Part | Qty | Notes | ~$ |
|---|------|-----|-------|-----|
| 9 | **HDMI monitor 21–32″** or MagicMirror-class panel | 1 | PyQt6 fullscreen Headspaces UI | 80–250 |
| 10 | HDMI cable + mount/stand | 1 | Wall mount optional | 15–40 |

### Network / mesh

| # | Part | Qty | Notes | ~$ |
|---|------|-----|-------|-----|
| 11 | Ethernet preferred **or** reliable Wi-Fi | 1 | Neighbors LAN mesh uses UDP beacon (default port **4177**) | 0–15 |
| 12 | Optional: second AMI on same LAN | — | Proves local neighbors without subscription | — |

### Optional household UPS

| # | Part | Qty | Notes | ~$ |
|---|------|-----|-------|-----|
| 13 | Small UPS for Pi + monitor | 0–1 | Not battery-pocket; graceful outage only | 40–120 |

### **Rough kit total**

| Build | Range |
|-------|--------|
| Cloud-only kiosk (no HAT, USB audio, modest monitor) | **~$250–500** |
| Local-leaning (HAT + better disk + nicer glass) | **~$450–800** |

---

## Software stack on this kit

- OS: **Raspberry Pi OS 64-bit** (Desktop if using on-device PyQt glass; Lite + remote X only for headless dev)
- Python **3.11** (repo pin)
- Package manager: **uv**
- User data: `~/.ami/`
- Optional local LLM: **Ollama** on-box or on Stronghold LAN (`llm.backend: ollama`)
- Optional cloud: xAI / Anthropic keys in `~/.ami/.env`
- STT: `stt.backend: local` (faster-whisper when installed) or `google` (legacy cloud)
- Neighbors: enabled headspace; mesh does **not** require internet

---

## Assembly (v0)

1. Seat cooler on Pi 5.  
2. If using AI HAT+: attach via PCIe FFC **before** stuffing the case; confirm no 40-pin conflict with audio HAT.  
3. Flash OS; enable SSH; set locale/timezone.  
4. Connect HDMI glass + USB speakerphone (or wire I2S audio HAT per vendor docs).  
5. Ethernet to home LAN (same L2 as other AMI units for mesh).  
6. Clone repo, `make install` (or fixed `rpi_install.sh`).  
7. Copy `config_template.yaml` → `~/.ami/ami_config.yaml`; set `llm`, `stt`, `neighbors` blocks.  
8. `ami run` / systemd autostart when ready.  
9. Second unit: same image → `list_neighbors` should show the peer after both `announce_presence`.

---

## Non-goals for this BOM

- Pocket battery chassis (that is mobile-ami)  
- Requiring paid subscription for first boot  
- Forcing Hailo for Neighbors or cloud mode  
- Shipping a single SKU that merges narthex glass contracts (Hermes doorway stays parallel)

---

## Open decisions (Wil)

- [ ] Final glass: consumer HDMI vs MM two-way mirror kit  
- [ ] Default audio: USB speakerphone vs ReSpeaker family  
- [ ] Default `llm.backend`: `ollama` vs `xai` for family builds  
- [ ] Whether AI HAT is **in** the “standard” kit or **addon SKU** only  
