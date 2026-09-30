"""Integration tests for VisionGuard FastAPI endpoints."""
from fastapi.testclient import TestClient
from visionguard.api.app import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "OPERATIONAL"

def test_cameras_list():
    response = client.get("/api/cameras")
    assert response.status_code == 200
    cameras = response.json()
    assert len(cameras) >= 6
    assert cameras[0]["camera_id"] == "CAM-01"

def test_analytics_network():
    response = client.get("/api/analytics/network")
    assert response.status_code == 200
    data = response.json()
    assert "online_cameras" in data
    assert "hourly_trends" in data

def test_anpr_validate():
    response = client.post("/api/anpr/validate", json={"raw_text": "DL01AB1234"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid_format"] is True
    assert data["standardized_plate"] == "DL 01 AB 1234"

def test_assistant_query():
    response = client.post("/api/assistant/query", json={"query": "Which camera has highest congestion?"})
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert len(data["citations"]) > 0

def test_system_health():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
