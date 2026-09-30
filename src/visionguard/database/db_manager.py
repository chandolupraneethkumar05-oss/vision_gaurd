"""Database connection manager and data access methods for VisionGuard."""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from visionguard.config import DB_PATH, DATA_DIR, DEFAULT_CAMERAS, CAMERA_GRAPH_EDGES
from visionguard.database.schema import SCHEMA_SQL

class DatabaseManager:
    """Manages SQLite database operations, transactions, and spatial queries."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes tables, indices, and seeds default network data if empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(SCHEMA_SQL)
            conn.commit()

        self._seed_default_network()

    def _seed_default_network(self):
        """Seeds default smart-city camera nodes and road network graph if not present."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM cameras")
            if cursor.fetchone()["cnt"] == 0:
                for cam in DEFAULT_CAMERAS:
                    cursor.execute("""
                        INSERT OR REPLACE INTO cameras 
                        (camera_id, name, latitude, longitude, intersection, direction, road_segment, speed_limit_kmh, fps, resolution, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cam["camera_id"], cam["name"], cam["latitude"], cam["longitude"],
                        cam["intersection"], cam["direction"], cam["road_segment"],
                        cam["speed_limit_kmh"], cam["fps"], cam["resolution"], cam["status"]
                    ))

                for edge in CAMERA_GRAPH_EDGES:
                    seg_id = f"{edge['source']}->{edge['target']}"
                    cursor.execute("""
                        INSERT OR REPLACE INTO road_segments
                        (segment_id, source_cam, target_cam, distance_km, min_time_sec, max_time_sec, speed_limit_kmh)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        seg_id, edge["source"], edge["target"], edge["distance_km"],
                        edge["min_time_sec"], edge["max_time_sec"], 50.0
                    ))

                # Seed realistic security watchlist
                watchlist_items = [
                    ("DL 01 AB 1234", "White Toyota Fortuner SUV", "Wanted in Highway Armed Robbery Case #2026/89", "CRITICAL"),
                    ("MH 12 CD 5678", "Black Mahindra Scorpio", "Hit-and-Run Suspect at Barakhamba Junction", "HIGH"),
                    ("UP 16 XY 9999", "Silver Hyundai Creta", "Repeated Toll Evasion & Fake HSRP Number Plate", "MEDIUM"),
                    ("KA 05 MN 4321", "Red Honda City", "Reported Stolen from Embassy Parking Area", "HIGH")
                ]
                for plate, desc, reason, priority in watchlist_items:
                    cursor.execute("""
                        INSERT OR IGNORE INTO watchlist (plate_number, vehicle_desc, reason, priority)
                        VALUES (?, ?, ?, ?)
                    """, (plate, desc, reason, priority))

                conn.commit()

    # --- Cameras ---
    def get_all_cameras(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cameras ORDER BY camera_id")
            return [dict(row) for row in cursor.fetchall()]

    def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cameras WHERE camera_id = ?", (camera_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Road Segments ---
    def get_all_road_segments(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM road_segments")
            return [dict(row) for row in cursor.fetchall()]

    # --- Observations ---
    def insert_observation(self, obs: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO observations 
                (camera_id, timestamp, frame_id, track_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                 vehicle_class, confidence, estimated_speed, color, plate_text, plate_confidence, embedding_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                obs["camera_id"], obs.get("timestamp", datetime.now(timezone.utc).isoformat()),
                obs["frame_id"], obs["track_id"], obs["bbox_x1"], obs["bbox_y1"], obs["bbox_x2"], obs["bbox_y2"],
                obs["vehicle_class"], obs["confidence"], obs.get("estimated_speed", 0.0),
                obs.get("color", "unknown"), obs.get("plate_text"), obs.get("plate_confidence", 0.0),
                obs.get("embedding_json")
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_observations(self, limit: int = 50, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if camera_id:
                cursor.execute("""
                    SELECT * FROM observations WHERE camera_id = ? 
                    ORDER BY id DESC LIMIT ?
                """, (camera_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM observations ORDER BY id DESC LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- Vehicle Identity & Re-ID ---
    def upsert_vehicle_identity(self, identity: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicle_identities 
                (global_vehicle_id, primary_plate, vehicle_class, color, make_model, embedding_json, first_seen, last_seen, observation_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(global_vehicle_id) DO UPDATE SET
                    primary_plate = COALESCE(excluded.primary_plate, vehicle_identities.primary_plate),
                    last_seen = excluded.last_seen,
                    observation_count = vehicle_identities.observation_count + 1
            """, (
                identity["global_vehicle_id"], identity.get("primary_plate"), identity["vehicle_class"],
                identity.get("color"), identity.get("make_model"), identity.get("embedding_json"),
                identity.get("first_seen", datetime.now(timezone.utc).isoformat()),
                identity.get("last_seen", datetime.now(timezone.utc).isoformat())
            ))
            conn.commit()

    def get_all_identities(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicle_identities ORDER BY last_seen DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- Journeys ---
    def insert_journey(self, journey: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO journeys 
                (journey_id, global_vehicle_id, start_camera, end_camera, start_time, end_time, total_distance_km, avg_speed_kmh, trajectory_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                journey["journey_id"], journey["global_vehicle_id"], journey["start_camera"],
                journey["end_camera"], journey["start_time"], journey["end_time"],
                journey.get("total_distance_km", 0.0), journey.get("avg_speed_kmh", 0.0),
                json.dumps(journey["trajectory"]), journey.get("status", "COMPLETED")
            ))
            conn.commit()

    def get_journeys_by_vehicle(self, global_vehicle_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM journeys WHERE global_vehicle_id = ? ORDER BY start_time DESC", (global_vehicle_id,))
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                r["trajectory"] = json.loads(r["trajectory_json"])
                results.append(r)
            return results

    def get_all_journeys(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT j.*, v.primary_plate, v.vehicle_class, v.color
                FROM journeys j
                LEFT JOIN vehicle_identities v ON j.global_vehicle_id = v.global_vehicle_id
                ORDER BY j.start_time DESC LIMIT ?
            """, (limit,))
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                r["trajectory"] = json.loads(r["trajectory_json"])
                results.append(r)
            return results

    # --- Traffic Events & Watchlist ---
    def insert_event(self, event: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO traffic_events (event_id, event_type, severity, camera_id, timestamp, details_json, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event["event_id"], event["event_type"], event["severity"],
                event["camera_id"], event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                json.dumps(event.get("details", {})), event.get("resolved", 0)
            ))
            conn.commit()

    def get_traffic_events(self, limit: int = 50, unresolved_only: bool = False) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM traffic_events"
            params = []
            if unresolved_only:
                query += " WHERE resolved = 0"
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                r["details"] = json.loads(r["details_json"])
                results.append(r)
            return results

    def get_watchlist(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM watchlist WHERE active = 1 ORDER BY added_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def check_watchlist_hit(self, plate: str) -> Optional[Dict[str, Any]]:
        clean_plate = plate.replace(" ", "").replace("-", "").upper()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM watchlist WHERE REPLACE(REPLACE(plate_number, ' ', ''), '-', '') = ? AND active = 1", (clean_plate,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Audit Logs ---
    def add_audit_log(self, action: str, query_or_event: str, details: str = "", user_role: str = "operator"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (action, user_role, query_or_event, details)
                VALUES (?, ?, ?, ?)
            """, (action, user_role, query_or_event, details))
            conn.commit()

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

db = DatabaseManager()
