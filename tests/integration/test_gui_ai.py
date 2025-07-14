import pytest
from unittest.mock import Mock, patch, AsyncMock
from PyQt6.QtWidgets import QApplication
from ami.gui.main_window import MainWindow
from ami.protos.generated import gui_service_pb2
from ami.core import VoiceEvent, ProcessState

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

@pytest.mark.asyncio
async def test_gui_ai_voice_interaction(main_window):
    # Test the full voice interaction flow
    test_audio = bytes([0, 1, 2, 3])
    transcribed_text = "What is the time?"
    ai_response = "It is 3:00 PM"
    
    # Mock AI client responses
    main_window.ai_client.process_audio = AsyncMock(return_value=transcribed_text)
    main_window.ai_client.query = AsyncMock(return_value=ai_response)
    
    # Simulate hotword detection
    main_window.handle_voice_event(VoiceEvent.HOTWORD_DETECTED, None)
    assert main_window.popup is not None
    
    # Simulate audio transcription
    main_window.handle_voice_event(VoiceEvent.TRANSCRIPTION, transcribed_text)
    assert main_window.popup.current_text == transcribed_text

@pytest.mark.asyncio
async def test_gui_ai_grpc_interaction(main_window):
    # Test the gRPC-based interaction between GUI and AI
    test_query = "What's the weather?"
    ai_response = "The weather is sunny"
    
    # Mock AI client
    main_window.ai_client.query = AsyncMock(return_value=ai_response)
    
    # Simulate receiving transcription via gRPC
    main_window.handle_grpc_event(
        gui_service_pb2.EventType.TRANSCRIPTION_READY,
        test_query
    )
    
    # Verify the transcription was handled
    assert main_window.last_transcription == test_query
    
    # Simulate receiving AI response via gRPC
    main_window.handle_grpc_event(
        gui_service_pb2.EventType.AI_RESPONSE_READY,
        ai_response
    )
    
    # Verify the response was handled
    assert main_window.popup is not None