import sys
import signal
import multiprocessing as mp

from PyQt6.QtWidgets import QApplication
from gunicorn.config import argparse

from ami.interfaces.gui.main_window import MainWindow

def get_args():
    parser = argparse.ArgumentParser(description="Artificia lModular Intelligence")

    parser.add_argument(
        '--dev',
        '-d',
        action='store_true',
        default=False,
        help='Enable development mode'
    )

    return parser.parse_args()

def signal_handler(signum, frame):
    """Handle termination signals by closing the Qt application"""
    QApplication.quit()


def startup_setting():
    # Use spawn method for better cross-platform compatibility
    mp.set_start_method('spawn')

    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_prod():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Start the audio process after window is shown
    window.start()

    # Execute the application
    exit_code = app.exec()

    # Ensure cleanup happens before exit
    window.cleanup()

    q = window.children()[1].children()

    sys.exit(exit_code)

def run_dev():
    print("Dev mode on!")


if __name__ == '__main__':
    args = get_args()

    if args.dev:
        run_dev()
    else:
        run_prod()

