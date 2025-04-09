import pytest
from unittest.mock import Mock, AsyncMock, patch
from ami.ai.ai import AI, TemporalCommunications

@pytest.fixture
def temporal_comms():
    return TemporalCommunications()

@pytest.fixture
async def ai_instance():
    with patch('ami.ai.ai.Config') as mock_config:
        mock_config.return_value.enabled_headspaces = []
        ai = AI()
        yield ai
        await ai.channel.close()

def test_temporal_communications_subscribe(temporal_comms):
    callback = Mock()
    temporal_comms.subscribe("test_event", callback)
    assert "test_event" in temporal_comms.subscribers
    assert callback in temporal_comms.subscribers["test_event"]

def test_temporal_communications_publish(temporal_comms):
    callback = Mock()
    temporal_comms.subscribe("test_event", callback)
    test_data = {"key": "value"}
    temporal_comms.publish("test_event", test_data)
    callback.assert_called_once_with(test_data)

@pytest.mark.asyncio
async def test_ai_query_local_success(ai_instance):
    ai_instance.brain.query = Mock(return_value="Test response")
    response = await ai_instance.query("Test query")
    assert response == "Test response"
    ai_instance.brain.query.assert_called_once_with("Test query")

@pytest.mark.asyncio
async def test_ai_query_fallback_to_backend(ai_instance):
    ai_instance.brain.query = Mock(side_effect=Exception("Local processing failed"))
    ai_instance.backend_stub.Query = AsyncMock(
        return_value=Mock(response="Backend response")
    )
    response = await ai_instance.query("Test query")
    assert response == "Backend response"

@pytest.mark.asyncio
async def test_ai_process_audio(ai_instance):
    test_audio = bytes([0, 1, 2, 3])
    ai_instance.backend_stub.ProcessAudio = AsyncMock(
        return_value=Mock(text="Transcribed text")
    )
    result = await ai_instance.process_audio(test_audio)
    assert result == "Transcribed text"

@pytest.mark.asyncio
async def test_ai_generate_audio(ai_instance):
    test_text = "Test text"
    test_audio = bytes([0, 1, 2, 3])
    ai_instance.backend_stub.GenerateAudio = AsyncMock(
        return_value=Mock(audio_data=test_audio)
    )
    result = await ai_instance.generate_audio(test_text)
    assert result == test_audio