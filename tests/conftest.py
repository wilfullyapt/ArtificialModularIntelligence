import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from fastapi.testclient import TestClient
from ami.backend.main import create_app
from ami.ai.ai import AI

@pytest.fixture(scope="session")
def qapp():
    """Global Qt application fixture"""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
async def ai_instance():
    """AI instance fixture with mocked config"""
    with patch('ami.ai.ai.Config') as mock_config:
        mock_config.return_value.enabled_headspaces = []
        ai = AI()
        yield ai
        await ai.channel.close()

@pytest.fixture
def backend_client():
    """FastAPI test client fixture"""
    app = create_app(
        enable_markdown=True,
        enable_logs=True,
        enable_settings=True
    )
    return TestClient(app)

@pytest.fixture
def mock_config():
    """Mock configuration fixture"""
    with patch('ami.config.Config') as mock:
        mock.return_value.enabled_headspaces = []
        mock.return_value.get.return_value = {}
        yield mock