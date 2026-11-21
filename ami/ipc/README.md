*IPC related events and states*

# Overview

## Major components

- **AI** subprocess — listener + brain + headspaces  
- **Flask** backend subprocess — blueprints / LAN helpers  
- **GUI** main process — PyQt glass  

`IPCManager` is constructed in the parent and passed into children; multiprocessing primitives (queues, shared state) are what actually cross the process boundary.

## What is live vs sketch

| Mechanism | Status |
|-----------|--------|
| Per-process **event queues** + `@on_event` handlers | **Live** — hotword, transcription, response, reload GUI, stop |
| `EventType` + `StateType` enums | **Live** for events; state machine only partly drives behavior |
| `EventPriority` on event types | **Defined but unused** — queues are plain FIFO; do not build priority scheduling on this yet |
| `command_queues` (RPC request/response) | **Scaffold only** — almost no production callers; prefer events until RPC is real |
| Config/plugin filesystem watchers | **Partial** — watcher exists; AI hot-reload handlers often TODO |

## Architecture (intended)

### Pub/Sub (event queue) — primary

- One-to-many notifications  
- Used for interaction and UI  

### RPC (command queue) — future

- One-to-one, expects response  
- Not required for current voice turn path  

When adding IPC features, extend **events** first unless you need a typed request/response.
