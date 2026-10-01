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

            # Seed realistic security watchlist if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM watchlist")
            if cursor.fetchone()["cnt"] == 0:
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

            # Seed sample E-Challans under Indian Motor Vehicles Act 2019 if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM echallans")
            if cursor.fetchone()["cnt"] == 0:
                challans = [
                    ("DL-ECH-2026-08192", "HR 26 DQ 7712", "OVERSPEEDING", "Sec 183(1) Motor Vehicles Act", 2000, "CAM-01", "Outer Circle Radial", 78.4, 50.0, "PENDING_PAYMENT", "Speed measured via calibrated ANPR tracker; exceeded limit by 28.4 km/h"),
                    ("DL-ECH-2026-08193", "DL 08 SC 1120", "NO_HELMET", "Sec 194D Motor Vehicles Act", 1000, "CAM-03", "Janpath Crossing", 38.0, 50.0, "PENDING_PAYMENT", "Rider and pillion observed without BIS standard protective headgear"),
                    ("DL-ECH-2026-08194", "UP 16 XY 9999", "RED_LIGHT_JUMP", "Sec 184 Motor Vehicles Act", 5000, "CAM-02", "Barakhamba Road", 42.1, 50.0, "PAID", "Violated red signal phase; crossed stop line during pedestrian clearance"),
                    ("DL-ECH-2026-08195", "DL 01 AB 1234", "DANGEROUS_DRIVING", "Sec 184 Motor Vehicles Act", 5000, "CAM-06", "C-Hexagon Roundabout", 82.0, 50.0, "PENDING_PAYMENT", "Reckless zigzag maneuvering at roundabout approach lane")
                ]
                for c_no, pl, v_type, sec, fine, cam, inter, spd, lim, st, notes in challans:
                    cursor.execute("""
                        INSERT OR IGNORE INTO echallans 
                        (challan_no, plate_number, violation_type, section_act, fine_amount, camera_id, intersection, recorded_speed, speed_limit, status, evidence_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (c_no, pl, v_type, sec, fine, cam, inter, spd, lim, st, notes))

            # Seed PCR Patrol Units if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM pcr_units")
            if cursor.fetchone()["cnt"] == 0:
                pcr_data = [
                    ("PCR-Alpha-01", "EAGLE-ONE", "Inspector R. K. Sharma", "CAM-01", 28.6328, 77.2197, "ON_PATROL"),
                    ("PCR-Bravo-02", "COBRA-TWO", "Sub-Inspector Vikram Singh", "CAM-02", 28.6294, 77.2274, "STANDBY"),
                    ("PCR-Charlie-03", "FALCON-THREE", "ASI Manjeet Dahiya", "CAM-04", 28.6253, 77.2215, "INTERCEPT_READY"),
                    ("PCR-Delta-04", "CHEETAH-FOUR", "Head Constable Amit Rawat", "CAM-06", 28.6129, 77.2295, "ON_PATROL")
                ]
                for uid, cs, off, junc, lat, lon, st in pcr_data:
                    cursor.execute("""
                        INSERT OR IGNORE INTO pcr_units (unit_id, call_sign, officer_in_charge, current_junction, latitude, longitude, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (uid, cs, off, junc, lat, lon, st))

            # Seed sample Green Corridor if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM green_corridors")
            if cursor.fetchone()["cnt"] == 0:
                cursor.execute("""
                    INSERT OR IGNORE INTO green_corridors 
                    (corridor_id, name, emergency_type, vehicle_plate, origin_cam, dest_cam, route_json, status, priority_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "GC-2026-004", "Connaught Place -> AIIMS Trauma Centre Corridor", "AMBULANCE", "DL 01 AM 9110",
                    "CAM-01", "CAM-06", '["CAM-01", "CAM-02", "CAM-04", "CAM-06"]', "ACTIVE", "CRITICAL_LEVEL_1"
                ))

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

    # --- Traffic Police Operations & E-Challans ---
    def get_echallans(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM echallans ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def insert_echallan(self, challan: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO echallans 
                (challan_no, plate_number, violation_type, section_act, fine_amount, camera_id, intersection, recorded_speed, speed_limit, status, officer_badge, evidence_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                challan["challan_no"], challan["plate_number"], challan["violation_type"],
                challan["section_act"], challan["fine_amount"], challan["camera_id"],
                challan["intersection"], challan.get("recorded_speed", 0.0), challan.get("speed_limit", 50.0),
                challan.get("status", "PENDING_PAYMENT"), challan.get("officer_badge", "DEL-TP-7429"),
                challan.get("evidence_notes", "")
            ))
            conn.commit()

    def update_challan_status(self, challan_no: str, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE echallans SET status = ? WHERE challan_no = ?", (status, challan_no))
            conn.commit()

    # --- Emergency Green Corridors ---
    def get_green_corridors(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM green_corridors ORDER BY activated_at DESC")
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                r["route"] = json.loads(r["route_json"]) if r.get("route_json") else []
                results.append(r)
            return results

    def activate_green_corridor(self, corridor: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO green_corridors
                (corridor_id, name, emergency_type, vehicle_plate, origin_cam, dest_cam, route_json, status, priority_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                corridor["corridor_id"], corridor["name"], corridor["emergency_type"],
                corridor.get("vehicle_plate", "EMERGENCY-01"), corridor["origin_cam"], corridor["dest_cam"],
                json.dumps(corridor["route"]), corridor.get("status", "ACTIVE"), corridor.get("priority_level", "CRITICAL_LEVEL_1")
            ))
            conn.commit()

    def deactivate_green_corridor(self, corridor_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE green_corridors SET status = 'COMPLETED' WHERE corridor_id = ?", (corridor_id,))
            conn.commit()

    # --- PCR Patrol Units ---
    def get_pcr_units(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pcr_units ORDER BY unit_id")
            return [dict(row) for row in cursor.fetchall()]

    def update_pcr_unit(self, unit_id: str, status: str, current_junction: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if current_junction:
                cursor.execute("""
                    UPDATE pcr_units SET status = ?, current_junction = ?, last_update = CURRENT_TIMESTAMP WHERE unit_id = ?
                """, (status, current_junction, unit_id))
            else:
                cursor.execute("""
                    UPDATE pcr_units SET status = ?, last_update = CURRENT_TIMESTAMP WHERE unit_id = ?
                """, (status, unit_id))
            conn.commit()

db = DatabaseManager()

