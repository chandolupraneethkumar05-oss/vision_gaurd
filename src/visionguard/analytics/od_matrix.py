"""Origin-Destination (OD) Matrix Calculator.
Analyzes traffic trips between urban intersections to identify peak movement corridors.
"""
from typing import Dict, Any, List
from collections import defaultdict
from visionguard.database.db_manager import db

class OriginDestinationAnalyzer:
    """Computes Origin-Destination trip distribution matrices across camera intersections."""

    @staticmethod
    def compute_matrix() -> Dict[str, Any]:
        """
        Calculates trip counts and average travel times between all camera pairs
        using reconstructed journey records.
        """
        journeys = db.get_all_journeys(limit=500)
        cameras = db.get_all_cameras()
        cam_ids = [c["camera_id"] for c in cameras]

        trip_counts = defaultdict(lambda: defaultdict(int))
        trip_durations = defaultdict(lambda: defaultdict(list))

        for j in journeys:
            src = j["start_camera"]
            dst = j["end_camera"]
            if src in cam_ids and dst in cam_ids:
                trip_counts[src][dst] += 1
                trip_durations[src][dst].append(j.get("avg_speed_kmh", 40.0))

        # Build tabular matrix and top corridor list
        matrix_rows = []
        corridor_list = []

        for src in cam_ids:
            row_data = {"origin": src}
            for dst in cam_ids:
                count = trip_counts[src][dst]
                row_data[dst] = count
                if src != dst and count > 0:
                    speeds = trip_durations[src][dst]
                    avg_speed = sum(speeds) / len(speeds) if speeds else 40.0
                    corridor_list.append({
                        "origin": src,
                        "destination": dst,
                        "trip_count": count,
                        "corridor_avg_speed": round(avg_speed, 1)
                    })
            matrix_rows.append(row_data)

        # Sort top corridors by trip volume
        corridor_list.sort(key=lambda x: x["trip_count"], reverse=True)

        return {
            "cameras": cam_ids,
            "matrix": matrix_rows,
            "top_corridors": corridor_list[:8]
        }
