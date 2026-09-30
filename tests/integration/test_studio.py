"""Integration tests for AI Video & Webcam Studio API endpoints."""
import cv2
import numpy as np
import base64
from fastapi.testclient import TestClient
from visionguard.api.app import app

client = TestClient(app)

def create_synthetic_frame_base64():
    """Generates a synthetic frame with vehicles and encodes to base64."""
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    # Road background
    img[120:, :] = 45
    # Two vehicles
    cv2.rectangle(img, (80, 150), (180, 220), (240, 240, 240), -1)   # White Car
    cv2.rectangle(img, (260, 160), (380, 250), (30, 130, 30), -1)    # Green Bus
    
    _, buf = cv2.imencode('.jpg', img)
    return f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"

def test_studio_sample_scenes():
    response = client.get("/api/studio/samples")
    assert response.status_code == 200
    data = response.json()
    assert "scenes" in data
    assert len(data["scenes"]) >= 3

def test_studio_sample_scene_image():
    response = client.get("/api/studio/sample-scene/sample-delhi-arterial")
    assert response.status_code == 200
    data = response.json()
    assert data["scene_id"] == "sample-delhi-arterial"
    assert data["image_base64"].startswith("data:image/jpeg;base64,")

def test_studio_detect_frame():
    b64_img = create_synthetic_frame_base64()
    payload = {
        "image_base64": b64_img,
        "confidence": 0.20,
        "detect_plates": True
    }
    response = client.post("/api/studio/detect-frame", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "inference_ms" in data
    assert "annotated_image" in data
    assert data["annotated_image"].startswith("data:image/jpeg;base64,")
    assert "detections" in data
