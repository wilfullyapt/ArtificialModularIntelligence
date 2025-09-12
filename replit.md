# replit.md

## Overview

**Artificial Modular Intelligence (AMI)** is a modular AI companion system designed to run on a Raspberry Pi with a plugin architecture called "Headspaces". Each Headspace can include visual GUI components, web endpoints, and LLM-driven agents. The system provides capabilities like timers, reminders, note-taking, financial assistance, media playback, and calendar integration. AMI operates as multiple independent processes communicating through well-defined IPC mechanisms.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Multi-Process Architecture
The system operates as three independent processes that communicate through multiprocessing IPC:
- **AI Process**: Handles voice interaction, STT/TTS, hotword detection, and LLM inference
- **GUI Process**: PyQt6-based full-screen interface with flexible widget positioning
- **Flask Backend Process**: Web server providing REST APIs and plugin web interfaces

### Plugin System (Headspaces)
The core architectural pattern is the "Headspace" plugin system where each plugin can implement up to three components:
- **Headspace Agent**: LLM-driven agent with tool calling capabilities
- **GUI Widget**: PyQt6 visual component with flexible positioning
- **Blueprint**: Flask web interface with routing

### State Management and Communication
- **IPC Manager**: Centralized communication broker using multiprocessing primitives
- **Event-Driven Architecture**: Pub/sub pattern for state changes and notifications
- **Command Queue System**: RPC-style communication for function calls between processes

### Core Components
- **Config System**: YAML-based configuration with real-time file watching
- **Plugin Registry**: Dynamic loading and management of builtin and third-party plugins
- **Conversation Management**: JSON-based conversation history with persistence
- **Logger System**: Loguru-based logging with script-specific log files

### Audio Processing Pipeline
- **Hotword Detection**: Local processing using openWakeWord
- **Voice Activity Detection**: Silero-VAD for local STT
- **LLM Integration**: Support for XAI, Anthropic, and OpenAI providers

### GUI Architecture
- **Flexible Layout System**: Custom layout manager supporting both absolute and relative positioning with anchor points
- **Widget Management**: Named widget indexing with dynamic reloading capabilities
- **Popup System**: Dialog management for AI interactions with conversation history

## External Dependencies

### Core Technologies
- **PyQt6**: GUI framework for the main interface
- **Flask**: Web server framework for blueprint components
- **Multiprocessing**: Native Python IPC for process communication
- **Pydantic**: Data validation and settings management
- **Loguru**: Advanced logging capabilities

### AI and Audio Processing
- **openWakeWord**: Local hotword detection
- **silero-vad**: Voice activity detection for STT
- **speech_recognition**: Speech-to-text processing
- **LLM Providers**: XAI/Anthropic/OpenAI APIs for language model inference

### Data Management
- **YAML**: Configuration file format
- **JSON**: Conversation persistence and plugin metadata
- **Markdown**: Note-taking and documentation format

### Development and Build Tools
- **Poetry**: Python dependency management
- **Make**: Build system for C components
- **GCC**: C compiler for CLI binary
- **UV**: Python package manager for development

### Third-Party Integrations
- **Git**: Plugin version control and updates
- **GitHub**: Plugin distribution and headspace downloading
- **Google Calendar**: Calendar synchronization (via AMI-Calendar plugin)
- **Spotify/YouTube**: Media playback capabilities

### System Dependencies
- **systemd**: Service management for autostart functionality
- **Watchdog**: File system monitoring for configuration changes
- **QR Code Generation**: For sharing web interfaces
- **cURL**: HTTP requests in C CLI components