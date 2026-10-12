"""Health endpoint regression check; no Ollama or database needed."""
from fastapi.testclient import TestClient
from app.main import app


def test_health_status():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
