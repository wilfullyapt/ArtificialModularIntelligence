import sys
import signal
import multiprocessing as mp

from PyQt6.QtWidgets import QApplication

from ami.interfaces.gui.main_window import MainWindow

def signal_handler(signum, frame):
    """Handle termination signals by closing the Qt application"""
    QApplication.quit()

if __name__ == "__main__":
    # Use spawn method for better cross-platform compatibility
    mp.set_start_method('spawn')

    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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
