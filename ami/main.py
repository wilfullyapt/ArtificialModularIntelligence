import sys
import signal
import traceback
import multiprocessing as mp
from concurrent import futures
import logging
import uvicorn
from typing import Optional, List
import argparse

from PyQt6.QtWidgets import QApplication
from ami.gui.main_window import MainWindow
from ami.ai.ai import AI
from ami.backend.main import app as fastapi_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.stop_events = {}
        self._shutdown_initiated = False

    def add_process(self, name: str, process: mp.Process, stop_event: Optional[mp.Event] = None):
        self.processes[name] = process
        if stop_event:
            self.stop_events[name] = stop_event

    def start_ai(self):
        stop_event = mp.Event()
        process = mp.Process(
            target=lambda: AI().run(),
            name="ai_process"
        )
        process.start()
        logger.info("AI process started")
        self.add_process("ai", process, stop_event)
        return process, stop_event

    def start_fastapi(self):
        stop_event = mp.Event()

        def run_fastapi():
            def handle_shutdown(signum, frame):
                logger.info("FastAPI shutdown signal received")
                stop_event.set()
                sys.exit(0)

            signal.signal(signal.SIGTERM, handle_shutdown)
            signal.signal(signal.SIGINT, handle_shutdown)

            config = uvicorn.Config(
                app=fastapi_app,
                host="0.0.0.0",
                port=58744,
                reload=False,
                log_level="info"
            )
            server = uvicorn.Server(config)
            server.run()

        process = mp.Process(
            target=run_fastapi,
            name="fastapi_process"
        )
        process.start()
        logger.info("FastAPI process started")
        self.add_process("fastapi", process, stop_event)
        return process, stop_event

    def start_gui(self):
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        window.start()
        return app, window

    def shutdown(self):
        if self._shutdown_initiated:
            return

        self._shutdown_initiated = True
        logger.info("Initiating graceful shutdown...")

        # First set all stop events
        for name, event in self.stop_events.items():
            logger.info(f"Signaling {name} to stop")
            event.set()

        # Then wait for processes to finish with timeout
        for name, process in self.processes.items():
            logger.info(f"Waiting for {name} to finish...")
            process.join(timeout=5)

            if process.is_alive():
                logger.warning(f"{name} didn't stop gracefully, terminating...")
                process.terminate()
                process.join(timeout=2)

                if process.is_alive():
                    logger.warning(f"{name} still alive after terminate, killing...")
                    process.kill()
                    process.join()

        logger.info("All processes stopped")

def get_args():
    parser = argparse.ArgumentParser(description="Artificial Modular Intelligence")
    parser.add_argument(
        '--dev',
        '-d',
        action='store_true',
        default=False,
        help='Enable development mode'
    )
    parser.add_argument(
        '--component',
        '-c',
        choices=['all', 'ai', 'backend', 'gui'],
        default='all',
        help='Specify which component to run (default: all)'
    )
    parser.add_argument(
        '--wait-deps',
        '-w',
        action='store_true',
        default=False,
        help='Wait for dependencies to be available before starting'
    )
    return parser.parse_args()

def signal_handler(signum, frame, process_manager, app=None):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}")
    if app:
        QApplication.quit()
    process_manager.shutdown()

def startup_settings():
    mp.set_start_method('spawn')

def run_app(dev_mode: bool = False, component: str = 'all', wait_deps: bool = False):
    """Run the application in either production or development mode"""
    startup_settings()
    process_manager = ProcessManager()

    try:
        # Start components based on selection
        if component in ['all', 'ai']:
            process_manager.start_ai()
            if wait_deps:
                import time
                time.sleep(2)  # Wait for AI service to be ready

        if component in ['all', 'backend']:
            process_manager.start_fastapi()
            if wait_deps:
                import time
                time.sleep(2)  # Wait for backend to be ready

        if component in ['all', 'gui']:
            # Set up signal handlers for GUI
            signal.signal(signal.SIGINT,
                        lambda s, f: signal_handler(s, f, process_manager, QApplication))
            signal.signal(signal.SIGTERM,
                        lambda s, f: signal_handler(s, f, process_manager, QApplication))

            app, window = process_manager.start_gui()

            if dev_mode:
                logger.info("Running in development mode")
                if component == 'all':
                    logger.info("AI server running on port 59195")
                    logger.info("FastAPI server running on port 58744")
                logger.info("Press Ctrl+C to exit")

            # Execute the GUI application
            exit_code = app.exec()

            # Cleanup
            window.cleanup()
            process_manager.shutdown()
            return exit_code

        # If not running GUI, just wait for signal
        else:
            signal.signal(signal.SIGINT,
                        lambda s, f: signal_handler(s, f, process_manager))
            signal.signal(signal.SIGTERM,
                        lambda s, f: signal_handler(s, f, process_manager))

            if dev_mode:
                logger.info("Running in development mode")
                if component in ['all', 'ai']:
                    logger.info("AI server running on port 59195")
                if component in ['all', 'backend']:
                    logger.info("FastAPI server running on port 58744")
                logger.info("Press Ctrl+C to exit")

            # Wait for signal
            signal.pause()

        return 0

    except Exception as e:
        logger.error(f"Error running application: {e}")
        process_manager.shutdown()
        return 1

if __name__ == '__main__':
    args = get_args()
    try:
        exit_code = run_app(
            dev_mode=args.dev,
            component=args.component,
            wait_deps=args.wait_deps
        )
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)