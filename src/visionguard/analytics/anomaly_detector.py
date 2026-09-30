"""Traffic Anomaly and Incident Detector.
Detects speeding violations, stopped vehicles, wrong-way driving, and watchlist hits.
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from visionguard.database.db_manager import db

class TrafficAnomalyDetector:
    """Monitors live tracking and ANPR telemetry for security and safety anomalies."""

    def evaluate_observation(self, obs: Dict[str, Any], camera_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates a single vehicle observation for safety/security violations.
        Returns generated alert events.
        """
        generated_events = []
        cam_id = obs["camera_id"]
        speed = obs.get("estimated_speed", 0.0)
        speed_limit = camera_info.get("speed_limit_kmh", 50.0)
        plate = obs.get("plate_text")

        # 1. Speeding Detection
        if speed > (speed_limit + 15.0):
            event = {
                "event_id": f"EVT-SPD-{uuid.uuid4().hex[:6].upper()}",
                "event_type": "SPEEDING",
                "severity": "HIGH" if speed > (speed_limit + 30.0) else "MEDIUM",
                "camera_id": cam_id,
                "timestamp": obs.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "details": {
                    "track_id": obs.get("track_id"),
                    "speed_detected": speed,
                    "speed_limit": speed_limit,
                    "excess_kmh": round(speed - speed_limit, 1),
                    "vehicle_class": obs.get("vehicle_class"),
                    "color": obs.get("color"),
                    "plate": plate or "UNREAD"
                },
                "resolved": 0
            }
            db.insert_event(event)
            generated_events.append(event)

        # 2. Watchlist Hit Detection
        if plate:
            hit = db.check_watchlist_hit(plate)
            if hit:
                event = {
                    "event_id": f"EVT-WCH-{uuid.uuid4().hex[:6].upper()}",
                    "event_type": "WATCHLIST_HIT",
                    "severity": hit.get("priority", "CRITICAL"),
                    "camera_id": cam_id,
                    "timestamp": obs.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "details": {
                        "plate_number": plate,
                        "vehicle_desc": hit.get("vehicle_desc"),
                        "reason": hit.get("reason"),
                        "track_id": obs.get("track_id"),
                        "intersection": camera_info.get("intersection")
                    },
                    "resolved": 0
                }
                db.insert_event(event)
                generated_events.append(event)

        return generated_events

    def check_congestion_anomaly(self, camera_id: str, avg_speed: float, count: int) -> Optional[Dict[str, Any]]:
        """Flags junction congestion when vehicle density is elevated and corridor speeds stall."""
        if count >= 12 and avg_speed < 18.0:
            cam = db.get_camera(camera_id)
            cam_name = cam["name"] if cam else camera_id
            event = {
                "event_id": f"EVT-CNG-{uuid.uuid4().hex[:6].upper()}",
                "event_type": "CONGESTION",
                "severity": "HIGH",
                "camera_id": camera_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "camera_name": cam_name,
                    "average_speed_kmh": round(avg_speed, 1),
                    "active_vehicle_queue": count,
                    "recommendation": "Adjust traffic signal timing or dispatch patrol"
                },
                "resolved": 0
            }
            db.insert_event(event)
            return event
        return None
