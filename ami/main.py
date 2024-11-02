import sys
from PyQt6.QtWidgets import QApplication
from ami.interfaces.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.start()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
