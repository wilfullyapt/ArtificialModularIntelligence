# Artificial Modular Intelligence 🧩🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AMI** is an AI companion with plug-n-play Headspaces with Headspace specific directory access. **AMI** is intended to be a voice companion that deploys a Flask server to her local network for more detailed interfacing with a visual tkinter element. **AMI** is built with the intention to be put on a Raspberry Pi with a monitor as an in home AI.

**Capabilities:**
- Basic voice assistant calendar + Google Calendar sycing
- Basic voice assistant for Markdown notes + downloading lists

### 🚀 Getting Started

#### Clone the repo
1. Make sure you have `git` and `make` installed
```bash
sudo apt-get update
sudo apt install git make
```
2. Clone the repo & `cd`: `git clone https://github.com/wilfullyapt/ArtificialModularIntelligence.git && cd ArtificialModularIntelligence`
3. Install AMI via Make: `make full-install`
4. (optional) Create the service autostart file & reboot
5. run `make run`

### 🔮 ML Models at work
- Hot Word / Wake word detection (local): [openWakeWord](https://github.com/dscripka/openWakeWord)
- Speech to Text (STT): Sphinx (local) or Google (cloud) => [SpeechRecognition](https://github.com/Uberi/speech_recognition).Recognizer()
- LLM Inference: [LangChain](https://github.com/langchain-ai/langchain) (local) & [TogetherAI](https://api.together.xyz/) (cloud / actual inference)


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

## Changelog
1. Implemented OpenWakeWord for hotword detection
2. Utils Headspace added for config editing through Flask server
3. Calendar syncing with Google Calendar + Ledgend
4. Redesigned basically the entire app


### Developer Notes
- Possible switch from Tkinter to PyQt6
- Better JSON infrastructure for calendar
- Utils and Time need to be rolled into `builtin`
- Local inference for STT needed
- Build Finacial Headspace
- Build Media Headspace
