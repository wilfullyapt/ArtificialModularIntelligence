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
│   ├── backend/                    # FastAPI backend
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI app entry point
│   │   ├── routes/                 # API routes
│   │   │   └── api.py
│   │   └── grpc_client.py          # gRPC client to call AI service
│   ├── gui/                        # PyQt6 GUI
│   │   ├── widgets/                # Widgets for the PyQT6 GUI
│   │   │   ├── base.py
│   │   │   └── builtins.py
│   │   ├── __init__.py
│   │   ├── main_window.py          # Main GUI window
│   │   ├── voice_input.py          # Voice capture logic
│   │   └── grpc_client.py          # gRPC client to call AI service
│   ├── protos/                     # gRPC protocol definitions
│   │   ├── ai_service.proto        # Defines AI service methods
│   │   └── generated/              # Generated Python code (via grpcio-tools)
│   │       ├── ai_service_pb2.py
│   │       └── ai_service_pb2_grpc.py
│   ├── headspacing/                # Builtin and imported headsapce functionality
│   │   ├── builtins/               # Builtin headspace functionality
│   │   └── base.py                 # Base components, for logging and config
│   ├── frontend/                   # React frontend that makes http calls to the backend
│   │   ├── src/                    # Source files for the react server
│   │── __init__.py
│   │── config.py                   # Config for the entire system
│   │── logging.py                  # logging for the entire system
│   │── main.py                     # Startup script
├── poetry.lock                     # Dependency lock file
├── pyproject.toml                  # Poetry config
├── .env                            # Environment variables (e.g., ports)
└── README.md                       # Project docs
```

## Architecture



## glue and connections

the things that connect all the architectures together

## NECESSARY

Take detailed notes of how this should work
Use this file as prompt injection
