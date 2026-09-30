"""Camera graph network with geospatial topology and travel-time constraints."""
import math
from typing import Dict, Any, List, Optional, Tuple
from visionguard.config import DEFAULT_CAMERAS, CAMERA_GRAPH_EDGES

class CameraGraph:
    """
    Represents the urban camera network as a directed topological graph with
    edge weights for road distances, allowed turns, and transit time windows.
    """

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._build_graph()

    def _build_graph(self):
        # Register nodes
        for cam in DEFAULT_CAMERAS:
            self.nodes[cam["camera_id"]] = cam

        # Register directed edges
        for edge in CAMERA_GRAPH_EDGES:
            src = edge["source"]
            tgt = edge["target"]
            dist = edge["distance_km"]
            min_t = edge["min_time_sec"]
            max_t = edge["max_time_sec"]

            # Bidirectional connectivity along arterial corridors
            self.edges[(src, tgt)] = {
                "distance_km": dist,
                "min_time_sec": min_t,
                "max_time_sec": max_t
            }
            self.edges[(tgt, src)] = {
                "distance_km": dist,
                "min_time_sec": min_t,
                "max_time_sec": max_t
            }

    def get_haversine_distance(self, cam1_id: str, cam2_id: str) -> float:
        """Computes Great Circle distance between two camera coordinates in kilometers."""
        if cam1_id not in self.nodes or cam2_id not in self.nodes:
            return 0.0
        c1 = self.nodes[cam1_id]
        c2 = self.nodes[cam2_id]

        lat1, lon1 = math.radians(c1["latitude"]), math.radians(c1["longitude"])
        lat2, lon2 = math.radians(c2["latitude"]), math.radians(c2["longitude"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371.0 # Earth radius in km
        return r * c

    def get_transit_constraints(self, cam_from: str, cam_to: str) -> Dict[str, Any]:
        """
        Retrieves min and max expected travel time between two cameras.
        If direct edge exists, uses road network parameters; otherwise estimates via Haversine.
        """
        if (cam_from, cam_to) in self.edges:
            return self.edges[(cam_from, cam_to)]
        
        # Estimate based on geographic distance assuming 40 km/h city average
        dist = self.get_haversine_distance(cam_from, cam_to)
        # Min speed 10 km/h (heavy traffic), Max speed 80 km/h (free flow speed limit)
        min_sec = (dist / 80.0) * 3600.0
        max_sec = (dist / 10.0) * 3600.0
        return {
            "distance_km": round(dist, 2),
            "min_time_sec": max(15.0, min_sec),
            "max_time_sec": max(120.0, max_sec)
        }

    def evaluate_spatio_temporal_feasibility(
        self,
        cam_from: str,
        cam_to: str,
        delta_time_seconds: float
    ) -> Tuple[float, str]:
        """
        Evaluates the physical probability score [0.0, 1.0] that a vehicle moved
        from cam_from to cam_to in delta_time_seconds.
        Eliminates 'teleportation' false positives!
        """
        if cam_from == cam_to:
            return (1.0, "SAME_CAMERA")

        constraints = self.get_transit_constraints(cam_from, cam_to)
        min_t = constraints["min_time_sec"]
        max_t = constraints["max_time_sec"]

        # Physically impossible speed (e.g. moved 2km in 10 seconds)
        if delta_time_seconds < (min_t * 0.8):
            return (0.0, f"PHYSICALLY_IMPOSSIBLE_SPEED ({delta_time_seconds:.1f}s < min {min_t:.1f}s)")

        # Within optimal expected transit window
        if min_t <= delta_time_seconds <= max_t:
            # Gaussian bell peak around median travel time
            median_t = (min_t + max_t) / 2.0
            sigma = (max_t - min_t) / 4.0
            score = math.exp(-0.5 * ((delta_time_seconds - median_t) / sigma)**2)
            return (max(0.65, min(1.0, score)), "OPTIMAL_TRAVEL_WINDOW")

        # Delayed transit (e.g. stopped at shop or traffic jam)
        if delta_time_seconds > max_t:
            decay_factor = max_t / delta_time_seconds
            score = max(0.15, 0.65 * decay_factor)
            return (score, "EXTENDED_TRAVEL_TIME")

        return (0.4, "BORDERLINE_TRANSIT")
