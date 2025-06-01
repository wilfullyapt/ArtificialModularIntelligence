import os
import sys
import signal
import traceback
from typing import Any, Optional
import multiprocessing as mp

from PyQt6.QtWidgets import QApplication
from watchdog.observers import Observer

from ami.core import Config, ConfigMetadataPluginWatcher, Conversation
from ami.core.registry import PluginVertical
from ami.ipc import IPCManager, ProcessType
from ami.ai import AI
from ami.gui import MainWindow as GUI
from ami.ipc import EventType, IPCEvent
from ami.llm.provider import LLMProvider

# Global variables for process management
ai: Optional[mp.Process] = None
should_exit = mp.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals with detailed info"""
    process = mp.current_process()
    process_name = process.name
    process_pid = os.getpid()
    print(f"\nShutdown signal received in process '{process_name}' (PID: {process_pid})...")
    print(f"SIGNUM: {signum}")
    print("Stack trace:")
    traceback.print_stack(frame)
    should_exit.set()

def cleanup():
    """Clean up all processes and observers"""
    should_exit.set()

    # Stop file system observer if it exists
    if 'observer' in globals() and observer.is_alive():
        observer.stop()
        observer.join(timeout=2)
        print("File system observer stopped")

    if ai:
        ai.join(timeout=5)
        print("AI process classed to join, 5 sec timeout")
        if ai.is_alive():
            ai.terminate()
            print("AI process terminated")
        print("AI process closed")
        print( " - - - - - - - - - - - - -")

def assign_file_watchers(ipc_manager: IPCManager):
    """ Create the Watcher Handler and schedule callbacks with an Observer """

    # Create the callback for the observer
    def broadcast_ipc_message(payload: Any) -> None:
        for process_type in ProcessType:
            if process_type is not ProcessType.SYSTEM:
                ipc_manager.send_event(
                    IPCEvent(
                        EventType.PLUGIN_METADATA_CHANGED, 
                        ProcessType.SYSTEM,
                        process_type,
                        payload
                    )
                )

        return              # Broadcast IPCEvent to all processes, return nothing

    config = Config()       # Initialize Config and Registry

    observer = Observer()
    handler = ConfigMetadataPluginWatcher(
        config_file=config.ami_config_filepath,
        metadata_file=config.plugin_metadata_filepath,
        plugins_dir=config.plugins_dir,
        callback=broadcast_ipc_message
    )
    observer.schedule(handler, str(config.ami_config_filepath), recursive=False)
    observer.schedule(handler, str(config.plugin_metadata_filepath), recursive=False)
    observer.schedule(handler, str(config.plugins_dir), recursive=False)
    observer.start()

if __name__ == '__main__':
    print(" --- DEV SCRIPT ---")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # ---   Interpeocess Communication Manager
    ipc_manager = IPCManager(stop_flag=should_exit)
#   assign_file_watchers(ipc_manager)

    run_ai = False
    run_gui = False
    run_backend = False

    run_ai = True
    run_gui = True
#   run_backend = True

    # ---   ARTIFICIAL INTELLIGENCE
    if run_ai:
        ai = AI(ipc_manager)
        if any([run_backend, run_gui]):
            ai.start()


    # ---   BACKEND FASTAPI
    if run_backend:
        backend = Backend(ipc_manager)
        backend.start()

    # ---   MAIN PROCESS GUI
    if run_gui:
        app = QApplication(sys.argv)
        window = GUI(ipc_manager)
        window.show()
        sys.exit(app.exec())
        

    sequential_debuging = False
#   sequential_debuging = True
    if sequential_debuging:

        # Route a query and return a headspace
#       hs = ai.brain.headspace_router("Set a reminder to take a out the trash every sunday at 6pm.")

        # Query the headspace directly and return `steps` to be summarized and added to the convo
#       steps = ai.brain['DATETIME'].query("Set a reminder to take out the trash every Sunday night at 5pm.")

        # Query the brain, route to a headspace and return the `steps` and `summary`
#       steps, summ = ai.brain.query("Set a reminder to take out the trash every Sunday night at 5pm.")

        # Some checks on how the plugin registry is working in the background
#       vert = ai.brain.registry.get_plugins_by_vertical(PluginVertical.GUI)

        # Checking on the functionality of the Function Calling Agent
#       raw_output = 'Thought: The human wants to add "dog food" to a list they refer to as "Costco list". To ensure this list exists before proceeding, I should first check the available lists using the appropriate tool.\n\nAction:```json\n{"action": "list_lists", "args": {}}\n```'
#       from ami.llm.agents import parse_llm_output
#       thought, action = parse_llm_output(raw_output)




        print("Sequential debugging. Don't fuck it up.")
