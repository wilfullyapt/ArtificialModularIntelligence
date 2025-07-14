# Artificial Modular Intelligence 🧩🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AMI** is an AI companion with a plugin architecture called *Headspaces*. Headspaces can include 1 to 3 elements: Visual GUI, Web endpoint, and an LLM driven agent.
**AMI** is built with the intention to be put on a Raspberry Pi with a monitor as an in home AI.

**Capabilities:**
- Timer and Reminder (builtin Datetime Headspace)
- Notes and List capabilities, including downloading list for on the go (builtin Markdown Headspace)
- Finacial Assistant / Advisor (builtin Finance Headspace)
- Media player for YouTube or Spotify (builtin Media Headspace)
- Voice assistant calendar + Google Calendar sycing [AMI-Calendar](https://github.com/wilfullyapt/AMI-Calendar)

### 🚀 Getting Started

#### Clone the repo
1. Make sure you have `git` and `make` installed
```bash
sudo apt-get update
sudo apt install git make
```
2. Clone the repo & `cd`: `git clone https://github.com/wilfullyapt/ArtificialModularIntelligence.git && cd ArtificialModularIntelligence`
3. Install AMI via Make: `make full-install`
4. (optional) Create the service autostart file & reboot `ami autostart`
5. Run `ami`

### 🔮 ML Models at work
- Hot Word / Wake word detection (local): [openWakeWord](https://github.com/dscripka/openWakeWord)
- Voice Activity Detector & STT (local): [silero-vad](https://github.com/snakers4/silero-vad)
- LLM Inference: XAI or Anthropic or OpenAI


### 💻 AMI Directory Structure

This is the directory structure AMI has controlled access to via the AI and Headspace modules:

```
ArtificiakModularIntelligence/
 ├── filespace/ (name define in config.yaml)
 │    ├── headspaces/
 │    │    ├── calendar
 │    │    │    ├── config.yaml (local config copied from Hedaspace default_config.yaml)
 │    │    │    └── calendar.json
 │    │    ├── markdown/
 │    │    │    ├── config.yaml (local config copied from Hedaspace default_config.yaml)
 │    │    │    ├── techno_optimist.md
 │    │    │    └── effective_accelerationism.md
 │    │    └── rag (work in progress)
 │    │         ├── documents/
 │    │         └── vectorstores/
 │    ├── logs/
 │    ├── resources/
 │    │    ├── img_dump/ (used to store qr codes currently)
 │    │    └── models/ (contains model files for OpenWakeWord and futrue STT models)
 │    └── config.yaml (copied from root default_config.yaml)
 └── /ami
```

### 🧭 Roadmap
- [x] Config editor
- Self updating functionality
- [x] Sync calendar with user google/apple calendar
- Finacial Assisstant Headspace
- Conversational Headspace. Allow for a Headspace to get to know the user through conversation. Answer question about the device.
- Researcher Headspace (Perplexity style search, Perplexity level subject matter research document, RAG agent)
- GitHub Wiki entry tracking add-on modules
- Discord or Telegram Headspace

### ✨ Inspired by
- The entire e/acc community
- MagicMirror2
- Obsidian paradigm: File > App

### 🧩 Build your own Headspace
See ami.ai.headspace directory to understand how the GUI, Blueprint, and Headspace tie into the Headspace Module

### Developer Notes
- Possible switch from Tkinter to PyQt6
- Better JSON infrastructure for calendar
- Utils and Time need to be rolled into `builtin`
- Local inference for STT needed
- Build Finacial Headspace
- Build Media Headspace
