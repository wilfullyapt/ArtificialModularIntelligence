import os
import sys
import signal
import traceback
import multiprocessing as mp

from PyQt6.QtWidgets import QApplication

from .ipc import IPCManager
from .ai import AI
from .flask import FlaskManager
from .gui import MainWindow as GUI

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

def run():

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    ipc_manager = IPCManager(stop_flag=should_exit)

    ai: AI = AI(ipc_manager)
    ai.start()

    server: FlaskManager = FlaskManager(ipc_manager)
    server.start()

    app = QApplication(sys.argv)
    gui: GUI = GUI(ipc_manager)
    gui.run()
    sys.exit(app.exec())

if __name__ == '__main__':
    run()
