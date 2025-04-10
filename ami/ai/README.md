# AI Subsystem Architecture

The AI subsystem runs as a separate process and handles voice interaction, natural language processing, and module management. It communicates with the main GUI process via builtin multiprocessing library.

## Core Loop
The AI is intended to be ran it it's own process.
`ai.run()` is called in the new process via `ai.start()`.
The AI will thread the hotword detection and listening.
The Headspaces functionality is handled.

The core loop looks like this:
```
ai.run() [Called by ai.start()] ---> WAITING_HOTWORD[State]; AI State ready

HOTWORD_DETECTED[Event]         ---> LISTENING[State]
LISTENING_FINISHED[Event]       ---> PROCESSING[State]; STT function and ai.query()
RESPONDED[Event]                ---> RESPONDED[State]; Listening for continuation
INTERACTION_CONCLUDED[Event]    ---> WAITING_HOTWORD[State]; concluded
```

## Core Components

### State Management (`state.py`)
- Implements a Finite State Machine (FSM) with states:
  - `WAITING`: Default state, listening for wake word
  - `LISTENING`: Actively listening for user input
- State changes are broadcast to subscribers via gRPC

### Hotword Detection and STT (`listener.py`)
- Uses `openwakeword` for wake word detection
- Runs in a separate thread to continuously process audio
- Evenet triggers passed to thread from the AI class/process

### Event System (`events.py`)
- Implements the Observer pattern for internal communication
- Allows components to subscribe to and publish events
- Handles asynchronous communication between components

### Core AI (`ai.py`)
- Main orchestrator class that initializes and manages all components
- Handles module loading and management
- Processes input (both text and audio)
- Manages the lifecycle of all components

## Data Flow

1. **Wake Word Detection**:
   ```
   Audio Input -> HotwordDetector -> State Change -> GUI Notification
   ```

2. **Voice Processing**:
   ```
   SAudio Input -> ProcessAudio -> Query -> GenerateAudio -> Audio Output
   ```

3. **Text Processing**:
   ```
   Text Input -> Query -> Text/Audio Response
   ```

## Module System

The AI supports dynamic loading of "headspace" modules that can extend its functionality:

- Modules are loaded from `ami/headspace/core/`
- Each module can provide:
  - `headspace.py`: Core module functionality
  - `blueprint.py`: API endpoints
  - `gui.py`: GUI components
  - `prompts.py`: NLP prompts

## Queue System

The AI implements several queues for managing different types of operations:

1. **State Queue**: Manages state transitions and notifications
2. **Input Queue**: Handles incoming audio/text input
3. **Processing Queue**: Manages AI processing tasks
4. **Output Queue**: Handles response generation and delivery

## Usage

The AI subprocess is typically started by the main GUI process:

1. GUI process spawns AI subprocess
2. AI initializes all components
3. AI starts gRPC server
4. GUI connects to AI via gRPC
5. Communication flows through defined gRPC methods


# AI Control Paradigm

## Components
- Listener class
- Headspace calls
- Queue routing


