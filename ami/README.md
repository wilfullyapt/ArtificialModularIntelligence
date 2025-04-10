# --- DEV ONLY NOTES ---

## Directory structure

```
ArtificialModularIntelligence/
├── ami/                            # AMI as the AI is intended to be interfaced with
│   ├── ai/                         # AI service with STT/TTS
│   │   ├── __init__.py
│   │   ├── ai.py                   # Main AI logic entry point
│   │   ├── stt.py                  # Speech-to-Text module
│   │   ├── tts.py                  # Text-to-Speech module
│   │   └── grpc_server.py          # gRPC server for AI methods
│   ├── backend/                    # FastAPI backend (handles markdown and other APIs)
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── markdown_api.py         # Markdown-specific API endpoints
│   │   └── grpc_client.py          # gRPC client to call AI service
│   ├── gui/                        # PyQt6 GUI
│   │   ├── widgets/                # Widgets for the PyQT6 GUI
│   │   │   ├── base.py
│   │   │   └── builtins.py
│   │   ├── __init__.py
│   │   ├── main_window.py          # Main GUI window
│   │   └── grpc_client.py          # gRPC client to call AI service
│   ├── protos/                     # gRPC protocol definitions
│   │   ├── ai_service.proto        # Defines AI service methods
│   │   └── generated/              # Generated Python code (via grpcio-tools)
│   │       ├── ai_service_pb2.py
│   │       └── ai_service_pb2_grpc.py
│   ├── headspacing/                # Builtin and imported headspace functionality
│   │   ├── builtins/               # Builtin headspace functionality
│   │   └── base.py                 # Base components, for logging and config
│   ├── frontend/                   # React frontend that makes http calls to the backend
│   │   ├── src/                    # Source files for the react server
│   │   ├── package-lock.json
│   │   └── package.json
│   │── __init__.py
│   │── config.py                   # Config for the entire system
│   │── logging.py                  # logging for the entire system
│   │── main.py                     # Startup script with process management
├── poetry.lock                     # Dependency lock file
├── pyproject.toml                  # Poetry config
├── .env                            # Environment variables (e.g., ports)
└── README.md                       # Project docs
```

## Architecture

### Multiprocessing Communication
- There are inheriting objects and managing objects defined in the `/ipc` directory

## Architecture & Process Communication

The system operates as three independent processes that communicate through well-defined interfaces:

1. **AI Process**
   - Runs the core AI service with STT/TTS capabilities
   - Exposes gRPC server on port 59195
   - Handles AI-specific operations and state management
   - Communicates with GUI and Backend through gRPC

2. **Backend Process**
   - FastAPI server running on port 58744
   - Handles HTTP API requests from the frontend
   - Manages markdown files and other persistent data
   - Acts as gRPC client to AI service when needed
   - Provides CORS support for frontend integration

3. **GUI Process**
   - PyQt6-based user interface
   - Acts as gRPC client to AI service
   - Manages UI state and user interactions
   - Independent from voice processing (handled by AI)

## Inter-Process Communication Flow

The system uses gRPC for inter-process communication, defined by two main protocol files:

1. `ami/proto/ai_service.proto`: Defines the AI service interface
   - ProcessText: Text-based AI queries
   - ProcessAudio: Audio processing capabilities

2. `ami/proto/gui_service.proto`: Defines GUI event streaming
   - StreamEvents: Bidirectional streaming for UI updates
   - Supports states: IDLE, LISTENING, THINKING, SPEAKING
   - Event types: HOTWORD_DETECTED, TRANSCRIPTION_READY, etc.

Communication Flow:

```
GUI Process                    AI Process                    Backend Process
(PyQt6)                       (Core AI)                     (FastAPI)
   |                             |                              |
   |                             |                              |
[gui/grpc_client.py]  <---  [ai/grpc_server.py]  <---  [backend/grpc_client.py]
   |                             |                              |
   |                             |                              |
[gui/grpc_server.py]  --->  [core/grpc_client.py]               |
                                 |                              |
                                 |                              |
                            [core/grpc_server.py]               |
                                                                |
                                                        [backend/main.py]
                                                     (HTTP API for frontend)
```

Key Communication Paths:

1. GUI -> AI:
   - Sends audio/text queries via AIClient (gui/grpc_client.py)
   - Receives responses through StreamEvents (gui/grpc_server.py)

2. AI -> GUI:
   - Streams events (state changes, responses) via GUIClient
   - Handles audio processing and text generation

3. Backend -> AI:
   - Makes AI service calls for processing markdown and other data
   - Exposes HTTP API for frontend communication

Port Configuration:
- AI Service: Default port 50051 (configurable)
- GUI Service: Default port 50052 (configurable)
- Backend API: Port 58744 (for frontend communication)

## Development Guidelines

1. **Process Independence**
   - Each component should handle its own state
   - Use proper error handling and recovery
   - Implement graceful startup/shutdown
   - Follow service discovery patterns

2. **Communication Patterns**
   - Use gRPC for AI service communication
   - REST API for frontend-backend interaction
   - Event-driven state updates
   - Proper error propagation

3. **Testing Strategy**
   - Unit tests per component
   - Integration tests for communication
   - End-to-end testing
   - Performance benchmarking and profiling
