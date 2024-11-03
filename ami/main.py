import sys
import signal
from PyQt6.QtWidgets import QApplication
from ami.interfaces.gui.main_window import MainWindow

def signal_handler(signum, frame):
    QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.start()

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Use timer to allow Python interpreter to catch SIGINT
    timer = app.startTimer(500)
    app.exec()

if __name__ == "__main__":
    sys.exit(main())
