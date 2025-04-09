import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from ami.gui.main_window import MainWindow
from ami.protos.generated import gui_service_pb2

@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(qapp):
    with patch('ami.gui.main_window.Config') as mock_config:
        mock_config.return_value.enabled_headspaces = []
        mock_config.return_value.get.return_value = {}
        window = MainWindow()
        yield window
        window.cleanup()

def test_main_window_initialization(main_window):
    assert main_window.popup is None
    assert main_window.audio_process is None
    assert main_window.grpc_server is not None
    assert main_window.ai_client is not None

def test_handle_grpc_event_hotword(main_window):
    main_window.handle_grpc_event(gui_service_pb2.EventType.HOTWORD_DETECTED, None)
    assert main_window.popup is not None

def test_handle_grpc_event_transcription(main_window):
    test_text = "Test transcription"
    with patch.object(main_window, 'popup') as mock_popup:
        main_window.handle_grpc_event(gui_service_pb2.EventType.TRANSCRIPTION_READY, test_text)
        assert main_window.last_transcription == test_text
        mock_popup.show_human_message.assert_called_once_with(test_text)

def test_handle_grpc_event_ai_response(main_window):
    test_response = "Test AI response"
    with patch.object(main_window, 'popup') as mock_popup:
        main_window.handle_grpc_event(gui_service_pb2.EventType.AI_RESPONSE_READY, test_response)
        mock_popup.show_ai_message.assert_called_once_with(test_response, expand=True)

def test_cleanup(main_window):
    main_window.start()  # This creates the audio process
    assert main_window.audio_process is not None
    main_window.cleanup()
    assert main_window.audio_process is None