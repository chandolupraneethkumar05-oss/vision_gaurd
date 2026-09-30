"""Camera management and live stream endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any

from visionguard.database.db_manager import db
from visionguard.ingestion.stream_manager import stream_manager
from visionguard.analytics.traffic_engine import TrafficAnalyticsEngine

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])
analytics_engine = TrafficAnalyticsEngine()

@router.get("", response_model=List[Dict[str, Any]])
def list_cameras():
    """Returns all registered urban smart-junction cameras."""
    cams = db.get_all_cameras()
    results = []
    for c in cams:
        metrics = analytics_engine.get_live_camera_metrics(c["camera_id"])
        c_dict = dict(c)
        c_dict["metrics"] = metrics
        results.append(c_dict)
    return results

@router.get("/{camera_id}")
def get_camera_detail(camera_id: str):
    """Retrieves camera specifications and real-time corridor metrics."""
    cam = db.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    metrics = analytics_engine.get_live_camera_metrics(camera_id)
    return {**cam, "metrics": metrics}

@router.get("/{camera_id}/stream")
def get_camera_stream(camera_id: str):
    """Streams live multi-camera video feed in standard multipart JPEG format."""
    cam = db.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return StreamingResponse(
        stream_manager.get_mjpeg_stream(camera_id, cam["name"]),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
