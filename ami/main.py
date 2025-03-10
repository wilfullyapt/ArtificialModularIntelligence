import sys
import signal
import traceback
import multiprocessing as mp
from concurrent import futures
import logging
import uvicorn
from typing import Optional

from PyQt6.QtWidgets import QApplication
from gunicorn.config import argparse

from ami.gui.main_window import MainWindow
from ami.ai.ai import AI
from ami.api.main import app as fastapi_app

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
    return parser.parse_args()

def signal_handler(signum, frame, process_manager, app=None):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}")
    if app:
        QApplication.quit()
    process_manager.shutdown()

def startup_settings():
    mp.set_start_method('spawn')

    # Set up signal handling
#   signal.signal(signal.SIGINT, signal_handler)
#   signal.signal(signal.SIGTERM, signal_handler)

def run_app(dev_mode: bool = False):
    """Run the application in either production or development mode"""
    startup_settings()
    process_manager = ProcessManager()

    try:
        # Start AI and FastAPI processes
        process_manager.start_ai()
        process_manager.start_fastapi()

        # Wait for services to be ready
        import time
        time.sleep(2)

        # Set up signal handlers
        signal.signal(signal.SIGINT, 
                     lambda s, f: signal_handler(s, f, process_manager, QApplication))
        signal.signal(signal.SIGTERM, 
                     lambda s, f: signal_handler(s, f, process_manager, QApplication))

        # Start GUI
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        window.start()

        if dev_mode:
            logger.info("Running in development mode")
            logger.info("AI server running on port 59195")
            logger.info("FastAPI server running on port 58744")
            logger.info("Press Ctrl+C to exit")

        # Execute the application
        exit_code = app.exec()

        # Cleanup
        window.cleanup()
        process_manager.shutdown()
        return exit_code

    except Exception as e:
        logger.error(f"Error running application: {e}")
        process_manager.shutdown()
        return 1

if __name__ == '__main__':
    args = get_args()
    try:
        exit_code = run_app(dev_mode=args.dev)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
