import pytest
import sys

def test_qt_imports():
    """Test that PyQt6 imports work correctly"""
    from PyQt6.QtWidgets import QApplication
    # Create an application instance to ensure Qt is working
    app = QApplication.instance() or QApplication(sys.argv)
    assert app is not None

def test_main_window_import():
    """Test that the main window can be imported"""
    from ami.gui.main_window import MainWindow
    assert MainWindow is not None

def test_ai_import():
    """Test that the AI module can be imported"""
    from ami.ai.ai import AI
    assert AI is not None

def test_fastapi_import():
    """Test that the FastAPI app can be imported"""
    from ami.backend.main import app as fastapi_app
    assert fastapi_app is not None

if __name__ == '__main__':
    pytest.main([__file__])