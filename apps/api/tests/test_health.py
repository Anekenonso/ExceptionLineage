from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body():
    """GET /health returns the expected JSON body."""
    response = client.get("/health")
    data = response.json()
    assert data == {
        "status": "ok",
        "service": "exceptionlineage-api",
        "version": "0.1.0",
    }


def test_health_content_type():
    """GET /health returns JSON content type."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"
