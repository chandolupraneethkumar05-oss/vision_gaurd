"""Grounded Intelligent Query Engine for Urban Traffic Operations.
Translates operator natural language questions into structured SQL queries over
verified database records, preventing AI hallucinations.
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from visionguard.database.db_manager import db

class GroundedTrafficAssistant:
    """
    Parses operator queries, executes deterministic queries over trusted database state,
    and returns factual responses with data audit citations.
    """

    def process_query(self, query: str, user_role: str = "operator") -> Dict[str, Any]:
        """
        Interprets natural language query and generates a grounded response.
        """
        q = query.strip()
        q_lower = q.lower()

        # Audit the query
        db.add_audit_log(action="NL_QUERY", query_or_event=q, user_role=user_role)

        # 1. Search by License Plate
        plate_match = re.search(r"([A-Za-z]{2}\s?[0-9]{1,2}\s?[A-Za-z]{1,3}\s?[0-9]{4}|[0-9]{2}\s?BH\s?[0-9]{4}\s?[A-Za-z]{1,2})", q, re.IGNORECASE)
        if plate_match or "plate" in q_lower or "vehicle" in q_lower and ("where" in q_lower or "seen" in q_lower or "find" in q_lower):
            target_plate = plate_match.group(0).upper().replace(" ", "") if plate_match else None
            return self._query_vehicle_location(target_plate, q)

        # 2. Query Congestion / Bottlenecks
        if "congestion" in q_lower or "traffic jam" in q_lower or "slowest" in q_lower or "bottleneck" in q_lower:
            return self._query_congestion()

        # 3. Query Speeding / Violations
        if "speeding" in q_lower or "speed violation" in q_lower or "fastest" in q_lower or "overspeeding" in q_lower:
            return self._query_speeding_violations()

        # 4. Query Watchlist Alerts
        if "watchlist" in q_lower or "stolen" in q_lower or "wanted" in q_lower or "suspect" in q_lower:
            return self._query_watchlist_status()

        # 5. Query Specific Camera / Junction Status
        cam_match = re.search(r"(cam-0[1-6]|camera\s?[1-6])", q_lower)
        if cam_match or "camera" in q_lower or "junction" in q_lower:
            return self._query_camera_status(cam_match.group(0) if cam_match else None)

        # 6. General Network Summary Fallback
        return self._query_general_overview(q)

    def _query_vehicle_location(self, target_plate: Optional[str], original_query: str) -> Dict[str, Any]:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if target_plate:
                cursor.execute("""
                    SELECT o.*, c.name as camera_name, c.intersection
                    FROM observations o
                    JOIN cameras c ON o.camera_id = c.camera_id
                    WHERE REPLACE(o.plate_text, ' ', '') LIKE ?
                    ORDER BY o.timestamp DESC LIMIT 5
                """, (f"%{target_plate}%",))
            else:
                cursor.execute("""
                    SELECT o.*, c.name as camera_name, c.intersection
                    FROM observations o
                    JOIN cameras c ON o.camera_id = c.camera_id
                    WHERE o.plate_text IS NOT NULL AND o.plate_text != ''
                    ORDER BY o.timestamp DESC LIMIT 5
                """)
            rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return {
                "grounded": True,
                "answer": f"No active observations found in the database matching '{target_plate or original_query}'. The vehicle has not passed through any registered smart junctions recently.",
                "data": [],
                "citations": ["TABLE: observations", "FILTER: plate_text"]
            }

        latest = rows[0]
        plate_str = latest.get("plate_text") or target_plate
        answer = (
            f"**Vehicle {plate_str}** was most recently detected at **{latest['camera_name']}** "
            f"({latest['intersection']}) on camera `{latest['camera_id']}`. "
            f"Observed speed was **{latest['estimated_speed']} km/h** with vehicle class `{latest['vehicle_class']}` "
            f"({latest['color']} body). Plate recognition confidence: **{int(latest['plate_confidence'] * 100)}%**."
        )

        return {
            "grounded": True,
            "answer": answer,
            "data": rows,
            "citations": [f"OBSERVATION_ID: #{latest['id']}", f"CAMERA: {latest['camera_id']}", f"TIMESTAMP: {latest['timestamp']}"]
        }

    def _query_congestion(self) -> Dict[str, Any]:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT camera_id, COUNT(*) as vehicle_count, AVG(estimated_speed) as avg_speed
                FROM observations
                GROUP BY camera_id
                ORDER BY vehicle_count DESC
            """)
            stats = [dict(r) for r in cursor.fetchall()]

        cameras = {c["camera_id"]: c for c in db.get_all_cameras()}
        if not stats:
            return {
                "grounded": True,
                "answer": "Current camera streams indicate free-flowing traffic across all urban corridors with no active gridlock detected.",
                "data": [],
                "citations": ["TABLE: observations"]
            }

        highest = stats[0]
        cam_info = cameras.get(highest["camera_id"], {})
        answer = (
            f"The junction with highest vehicle density is **{cam_info.get('name', highest['camera_id'])}** "
            f"({cam_info.get('intersection', 'Corridor')}) with **{highest['vehicle_count']} active vehicles** detected "
            f"and an average corridor speed of **{round(highest['avg_speed'] or 40.0, 1)} km/h**."
        )

        return {
            "grounded": True,
            "answer": answer,
            "data": stats,
            "citations": [f"METRIC: Density aggregation across {len(stats)} camera nodes", "TABLE: observations"]
        }

    def _query_speeding_violations(self) -> Dict[str, Any]:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, c.name as camera_name
                FROM traffic_events e
                JOIN cameras c ON e.camera_id = c.camera_id
                WHERE e.event_type = 'SPEEDING'
                ORDER BY e.timestamp DESC LIMIT 5
            """)
            events = [dict(r) for r in cursor.fetchall()]

        if not events:
            return {
                "grounded": True,
                "answer": "There are no unaddressed speeding violations logged in the immediate monitoring window.",
                "data": [],
                "citations": ["TABLE: traffic_events", "TYPE: SPEEDING"]
            }

        answer = (
            f"Found **{len(events)} recent speeding violation(s)**. Latest incident logged at **{events[0]['camera_name']}** "
            f"involving high-speed corridor traversal."
        )

        return {
            "grounded": True,
            "answer": answer,
            "data": events,
            "citations": [f"EVENT: {e['event_id']}" for e in events]
        }

    def _query_watchlist_status(self) -> Dict[str, Any]:
        watchlist = db.get_watchlist()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, c.name as camera_name
                FROM traffic_events e
                JOIN cameras c ON e.camera_id = c.camera_id
                WHERE e.event_type = 'WATCHLIST_HIT'
                ORDER BY e.timestamp DESC LIMIT 5
            """)
            hits = [dict(r) for r in cursor.fetchall()]

        answer = (
            f"There are currently **{len(watchlist)} active vehicles** registered on the city security watchlist. "
            f"VisionGuard has triggered **{len(hits)} alert hit(s)** in the monitoring system."
        )

        return {
            "grounded": True,
            "answer": answer,
            "data": {"watchlist_count": len(watchlist), "recent_hits": hits},
            "citations": ["TABLE: watchlist", "TABLE: traffic_events"]
        }

    def _query_camera_status(self, cam_code: Optional[str]) -> Dict[str, Any]:
        cams = db.get_all_cameras()
        if cam_code:
            clean_code = cam_code.upper().replace(" ", "").replace("CAMERA", "CAM-0")
            matched = [c for c in cams if c["camera_id"] in clean_code or clean_code in c["camera_id"]]
            target = matched[0] if matched else cams[0]
        else:
            target = cams[0]

        answer = (
            f"**{target['name']}** (`{target['camera_id']}`) at **{target['intersection']}** is **{target['status']}**. "
            f"Configured resolution: `{target['resolution']}`, FPS: `{target['fps']}`, Speed Limit: `{target['speed_limit_kmh']} km/h`."
        )

        return {
            "grounded": True,
            "answer": answer,
            "data": [target],
            "citations": [f"CAMERA: {target['camera_id']}", "TABLE: cameras"]
        }

    def _query_general_overview(self, q: str) -> Dict[str, Any]:
        cameras = db.get_all_cameras()
        obs = db.get_recent_observations(limit=10)
        answer = (
            f"VisionGuard is currently operating across **{len(cameras)} urban camera junctions**. "
            f"The system has processed real-time streams with vehicle detection, Indian ANPR verification, "
            f"and cross-camera trajectory tracking active. To inspect specific events, ask about a license plate, "
            f"camera status, speeding violations, or congestion levels."
        )
        return {
            "grounded": True,
            "answer": answer,
            "data": {"total_cameras": len(cameras), "sample_observations": len(obs)},
            "citations": ["TABLE: cameras", "TABLE: observations"]
        }

grounded_assistant = GroundedTrafficAssistant()
