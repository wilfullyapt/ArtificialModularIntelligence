
import os
import sys
import signal
import traceback
from typing import Optional
import multiprocessing as mp


from PyQt6.QtWidgets import QApplication

from ami.ipc import IPCManager
from ami.ai import AI
from ami.gui import MainWindow as GUI

# Global variables for process management
ai: Optional[mp.Process] = None
should_exit = mp.Event()

def import_dev_env():
    print(" -- ADD-ON IMPORT DEV ENVIORNMENT --")

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
    """Clean up all processes"""
    should_exit.set()

    if ai:
        ai.join(timeout=5)
        print("AI process classed to join, 5 sec timeout")
        if ai.is_alive():
            ai.terminate()
            print("AI process terminated")
        print("AI process closed")
        print( " - - - - - - - - - - - - -")

if __name__ == '__main__':
    print(" --- DEV SCRIPT ---")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # ---   Interpeocess Communication Manager
    ipc_manager = IPCManager(stop_flag=should_exit)

    run_ai = True
    run_backend = False
    run_gui = True

    try:
        # ---   ARTIFICIAL INTELLIGENCE
        if run_ai:
            ai = AI(ipc_manager)
            if any([run_backend, run_gui]):
                ai.start()

        # ---   BACKEND FASTAPI
#       if run_backend:
#           backend = Backend(ipc_manager)
#          backend.start()


        # ---   MAIN PROCESS GUI
        if run_gui:
            app = QApplication(sys.argv)
            window = GUI(ipc_manager)
            window.show()
            sys.exit(app.exec())

    finally:
#       cleanup()
        pass
