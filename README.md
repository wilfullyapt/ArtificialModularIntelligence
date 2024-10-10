# Artificial Modular Intelligence 🧩🧠

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AMI** is an AI companion with plug-n-play Headspaces with Headspace specific directory access. **AMI** is intended to be a voice companion that deploys a Flask server to her local network for more detailed interfacing with a visual tkinter element. **AMI** is built with the intention to be put on a Raspberry Pi with a monitor as an in home AI.

**Capabilities:**
- Basic voice assistant calendar
- Basic voice assistant markdown control
- RAG (Retrieval Augmented Generation) over your stored documents for Question Answering
*Coming soon*
- Financial Advisor: Upload your financial documents and gain insight and personalized financial guidance
- Integration and syncing with calendar apps like Google and Apple
- Sharable Picture Frame/Albums

### 🚀 Getting Started

#### Clone the repo
1. Clone the repo: `git clone https://github.com/wilfullyapt/ArtificialModularIntelligence.git`
2. Change directory: `cd ArtificialModularIntelligence`
3. Install: `./install.sh`
    - `sudo apt update && upgrade`
    - Creates a virtual enviornment
    - Installs all related packages
    - Copies a fresh `config.yaml` from template, unless one exists already
. Update `config.yaml` with TogertherAI key
5. Run the AI: `./run.sh`

### 🔮 ML Models at work
- Hot Word / Wake word detection (local): [openWakeWord](https://github.com/dscripka/openWakeWord)
- Speech to Text (STT): Sphinx (local) or Google (cloud) => [SpeechRecognition](https://github.com/Uberi/speech_recognition).Recognizer()
- LLM Inference: [LangChain](https://github.com/langchain-ai/langchain) (local) & [TogetherAI](https://api.together.xyz/) (cloud / actual inference)


### 💻 AMI Directory Structure

This is the directory structure AMI has controlled access to via the AI and Headspace modules:

```
ami/
 ├── filespace/ (name define in config.yaml)
 │    ├── headspaces/
 │    │    ├── calendar
 │    │    │    ├── calendar.json
 │    │    ├── markdown/
 │    │    │    ├── alpha.md
 │    │    │    ├── omega.md
 │    │    ├── rag
 │    │    │    ├── documents/
 │    │    │    ├── vectorstores/
 │    ├── logs/
 │    ├── recordings/
 │    ├── computer.umdl (from snowboy library)
```

### 🧭 Roadmap
- Tools Headspace (Calibrate Audio / Train new Hot Word, Config editor (core, headspaces, add-ons), self update, notifications)
- Finacial Assisstant Headspace
- Conversational Headspace. Allow for a Headspace to get to know the user through conversation. Answer question about the device.
- Researcher Headspace (Perplexity style search, Perplexity level subject matter research document, RAG agent)
- GitHub Wiki entry tracking add-on modules
- Discord or Telegram Headspace

### ✨ Inspired by
The entire e/acc community
MagicMirror2
Obsidian paradigm: File > App

### 🧩 Build your own Headspace
See ami.ai.headspace directory to understand how the GUI, Blueprint, and Headspace tie into the Headspace Module

## Changelog
1. Implemented OpenWakeWord for hotword detection
2. Utils Headspace added for config editing through Flask server
