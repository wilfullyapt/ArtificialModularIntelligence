import pytest
from fastapi.testclient import TestClient
from ami.backend.main import create_app

@pytest.fixture
def test_client():
    app = create_app(
        enable_markdown=True,
        enable_logs=True,
        enable_settings=True
    )
    return TestClient(app)

def test_health_check_all_enabled(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["markdown"] is True
    assert data["components"]["logs"] is True
    assert data["components"]["settings"] is True

def test_health_check_partial_enabled(test_client):
    app = create_app(
        enable_markdown=True,
        enable_logs=False,
        enable_settings=False
    )
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["markdown"] is True
    assert data["components"]["logs"] is False
    assert data["components"]["settings"] is False

def test_cors_headers(test_client):
    response = test_client.options("/health", headers={
        "Origin": "http://localhost:52563",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:52563"