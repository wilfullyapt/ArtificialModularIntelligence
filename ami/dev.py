import os
import sys
import signal
import traceback
from typing import Any, Tuple
import argparse
import multiprocessing as mp
from pprint import pprint as pp

from PyQt6.QtWidgets import QApplication
from watchdog.observers import Observer

from .core import Config, ConfigMetadataPluginWatcher
from .ipc import IPCManager, ProcessType, EventType, IPCEvent
from .ai import AI
from .gui import MainWindow as GUI
from .flask import FlaskManager

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

def search(obj: Any, srch_str: str):
    for item in dir(obj):
        if srch_str in item:
            print(f":::  '{item}'  :::  TYPE {type(getattr(obj, item))}")

def parse_args() -> Tuple[bool, bool, bool, bool]:
    """
    Three process test problem: Turn on one or two with the other[s] off.
    All processes default on, unless process specific command line args exists
    Turn on only the command line args
    """
    parser = argparse.ArgumentParser(description="Command-line argument parser for script configuration")
    parser.add_argument('--ai', action='store_true', help='Enable AI')
    parser.add_argument('--gui', action='store_true', help='Enable GUI')
    parser.add_argument('--server', action='store_true', help='Enable Flask server')
    parser.add_argument('--debug', action='store_true', help='Enable debugging')
    try:
        args = parser.parse_args()
    except:
        raise ValueError("Unknown arguement passed, the only acceptable arguements are: --ai --gui --server --debug")
    
    ai, gui, server = True, True, True
    debug = args.debug
    
    if sum([args.gui, args.ai, args.server]) in [1, 2]:
        gui = args.gui
        ai = args.ai
        server = args.server
    
    return gui, ai, server, debug

if __name__ == '__main__':
    print(" --- DEV SCRIPT ---")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # ---   Interpeocess Communication Manager
    ipc_manager = IPCManager(stop_flag=should_exit)
#   assign_file_watchers(ipc_manager)

    # ---   Booleen flag for dev running
    run_gui, run_ai, run_server, sequential_debuging = parse_args()

    # ---   ARTIFICIAL INTELLIGENCE
    if run_ai:
        ai: AI = AI(ipc_manager)
        if any([run_server, run_gui]):
            ai.start()

    # ---   BACKEND FASTAPI
    if run_server:
        server: FlaskManager = FlaskManager(ipc_manager)
        if any([run_ai, run_gui]):
            server.start()

    # ---   MAIN PROCESS GUI
    if run_gui:
        app = QApplication(sys.argv)
        gui: GUI = GUI(ipc_manager)
        if any([run_server, run_ai]):
            gui.run()
            sys.exit(app.exec())
        

    if sequential_debuging:

        # function for testing Event and Data combos to the AI
        def queue_event(event_type: EventType, data: Any):
            event = IPCEvent(type=event_type, source=ProcessType.AI, target=ProcessType.GUI, data=data)
            ai.get_queue(ProcessType.AI).put(event)

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

        # Tests a Transcription to the AI
#       queue_event(EventType.TRANSCRIPTION_READY, "add steak to the costco list")
#       ai.check_and_handle_incoming_ipc_event()

        # Markdown specific testing
#       md = ai.brain['markdown'].markdown


        flap = server.flask_app
        mdb = flap.blueprints['Markdown']


        print("Sequential debugging. Don't fuck it up.")
