
from fastapi.testclient import TestClient

from supportiq.main import app

client = TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
