"""Journey Reconstructor: Assembles multi-camera observations into spatio-temporal trajectories."""
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from visionguard.association.camera_graph import CameraGraph
from visionguard.database.db_manager import db

class JourneyReconstructor:
    """
    Reconstructs vehicle journeys across city cameras, calculating total trip distance,
    travel duration, average corridor speed, and generating GIS waypoints.
    """

    def __init__(self, camera_graph: Optional[CameraGraph] = None):
        self.camera_graph = camera_graph or CameraGraph()

    def reconstruct_from_observations(
        self,
        global_vehicle_id: str,
        observations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Takes a list of chronologically sorted observations for a vehicle
        and reconstructs the spatial journey.
        """
        if not observations or len(observations) < 1:
            return None

        # Sort observations by timestamp
        sorted_obs = sorted(observations, key=lambda x: x["timestamp"])

        waypoints = []
        total_distance_km = 0.0
        cams = self.camera_graph.nodes

        for idx, obs in enumerate(sorted_obs):
            cam_id = obs["camera_id"]
            cam_info = cams.get(cam_id, {})
            lat = cam_info.get("latitude", 28.6328)
            lon = cam_info.get("longitude", 77.2197)

            if idx > 0:
                prev_cam = sorted_obs[idx - 1]["camera_id"]
                step_dist = self.camera_graph.get_haversine_distance(prev_cam, cam_id)
                total_distance_km += step_dist

            waypoints.append({
                "camera_id": cam_id,
                "camera_name": cam_info.get("name", cam_id),
                "intersection": cam_info.get("intersection", "Urban Corridor"),
                "latitude": lat,
                "longitude": lon,
                "timestamp": obs["timestamp"],
                "speed_kmh": obs.get("estimated_speed", 40.0),
                "plate_confidence": obs.get("plate_confidence", 0.9)
            })

        start_time_str = sorted_obs[0]["timestamp"]
        end_time_str = sorted_obs[-1]["timestamp"]

        # Calculate transit duration
        try:
            t1 = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            duration_hours = max(0.001, (t2 - t1).total_seconds() / 3600.0)
            avg_speed = total_distance_km / duration_hours if total_distance_km > 0 else 35.0
        except Exception:
            avg_speed = 38.5

        journey_id = f"JRN-{uuid.uuid4().hex[:8].upper()}"
        journey_data = {
            "journey_id": journey_id,
            "global_vehicle_id": global_vehicle_id,
            "start_camera": sorted_obs[0]["camera_id"],
            "end_camera": sorted_obs[-1]["camera_id"],
            "start_time": start_time_str,
            "end_time": end_time_str,
            "total_distance_km": round(total_distance_km, 2),
            "avg_speed_kmh": round(min(120.0, max(15.0, avg_speed)), 1),
            "trajectory": waypoints,
            "status": "COMPLETED"
        }

        # Persist to database
        db.insert_journey(journey_data)
        return journey_data
