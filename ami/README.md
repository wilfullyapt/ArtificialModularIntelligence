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

### gRPC Communication
- AI service acts as gRPC server
- GUI and Backend act as gRPC clients
- Bidirectional streaming for real-time updates
- Handles state synchronization between processes

### HTTP Communication
- Backend provides REST API endpoints
- Frontend makes HTTP requests to backend
- Supports file uploads and markdown management
- CORS enabled for frontend access

## Process Management

The system uses a flexible process management approach:

1. **Development Mode**
   - Components can be run independently
   - Supports individual testing and debugging
   - Hot-reloading enabled for backend
   - Detailed logging and error reporting

2. **Production Mode**
   - Coordinated process startup/shutdown
   - Graceful termination handling
   - Resource cleanup on exit
   - Process health monitoring

3. **Component Testing**
   - Each process can be tested in isolation
   - Mock services available for dependencies
   - Configurable ports and endpoints
   - Environment-specific settings

## Configuration Management

- Centralized configuration through config.py
- Environment variables via .env file
- Process-specific settings
- Logging configuration per component

## Startup Flow

1. Process Manager initializes
2. AI service starts first
3. Backend service starts second
4. GUI launches last after services are ready
5. Signal handlers set up for graceful shutdown

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
   - Performance benchmarking