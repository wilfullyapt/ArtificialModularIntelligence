import pytest
import asyncio
import grpc
from unittest.mock import patch, AsyncMock
from ami.ai.ai import AI
from ami.backend.main import create_app
from ami.protos.generated import ai_service_pb2, ai_service_pb2_grpc
from fastapi.testclient import TestClient

@pytest.fixture
async def ai_instance():
    with patch('ami.ai.ai.Config') as mock_config:
        mock_config.return_value.enabled_headspaces = []
        ai = AI()
        yield ai
        await ai.channel.close()

@pytest.fixture
def backend_client():
    app = create_app(enable_markdown=True, enable_logs=True, enable_settings=True)
    return TestClient(app)

@pytest.mark.asyncio
async def test_ai_backend_query_integration(ai_instance, backend_client):
    # Test that AI can query the backend service
    test_query = "What is the weather?"
    expected_response = "The weather is sunny"
    
    # Mock the gRPC stub response
    ai_instance.backend_stub.Query = AsyncMock(
        return_value=ai_service_pb2.QueryResponse(response=expected_response)
    )
    
    # Force AI to use backend by making local brain fail
    ai_instance.brain.query = AsyncMock(side_effect=Exception("Local processing failed"))
    
    # Make the query
    response = await ai_instance.query(test_query)
    assert response == expected_response

@pytest.mark.asyncio
async def test_ai_backend_audio_processing(ai_instance, backend_client):
    # Test audio processing integration
    test_audio = bytes([0, 1, 2, 3])
    expected_text = "Hello, world!"
    
    # Mock the gRPC stub response
    ai_instance.backend_stub.ProcessAudio = AsyncMock(
        return_value=ai_service_pb2.TranscriptionResponse(text=expected_text)
    )
    
    # Process audio
    result = await ai_instance.process_audio(test_audio)
    assert result == expected_text

@pytest.mark.asyncio
async def test_ai_backend_audio_generation(ai_instance, backend_client):
    # Test audio generation integration
    test_text = "Generate this audio"
    expected_audio = bytes([4, 5, 6, 7])
    
    # Mock the gRPC stub response
    ai_instance.backend_stub.GenerateAudio = AsyncMock(
        return_value=ai_service_pb2.AudioResponse(audio_data=expected_audio)
    )
    
    # Generate audio
    result = await ai_instance.generate_audio(test_text)
    assert result == expected_audio