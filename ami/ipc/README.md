*IPC related events and states and described here*

# Overview

## Major Components

### The Big Three:
- The AI subprocess
- The FastAPI Backend subprocess
- The main process GUI

These elements share common components as far as IPC and should be though of similarly when working with these IPC components

### IPCManager
- The IPCManager in the `./manager.py` file
- Must be instanced before the Big Three and passed to each sub process

**Note**: the instance of the IPCManager is not shared to the other process, rather a proxy object, yet the members and components of the IPCManager are shared between process. This is the workaround.

### BaseProcess
- See `./base.py:BaseProcess`

This should be the parent class for the Big Three. The idea is to create a standard subprocessing class containing all the infrastructure necessary for IPC setup and looping. Between the the IPCManager being passed to the BaseProcess for management, all specfics coming from one of the Big Three should be contained to the `setup` and `loop` methods of the **BaseProcess**.

## Architecture

### Remote Procedure Call (RPC) (Command Queue)
- One-to-one communication
- Expects a response
- Used for function calls between processes

### Pub/Sub (Event Queue)
- One-to-many communication
- No response expected
- Used for state changes and notifications
