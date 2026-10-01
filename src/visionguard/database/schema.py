"""Database schema definitions for VisionGuard."""
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Camera Network Table
CREATE TABLE IF NOT EXISTS cameras (
    camera_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    intersection TEXT NOT NULL,
    direction TEXT NOT NULL,
    road_segment TEXT NOT NULL,
    speed_limit_kmh REAL DEFAULT 50.0,
    fps INTEGER DEFAULT 30,
    resolution TEXT DEFAULT '1920x1080',
    status TEXT DEFAULT 'ONLINE',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Road Topology / Spatial Constraints Table
CREATE TABLE IF NOT EXISTS road_segments (
    segment_id TEXT PRIMARY KEY,
    source_cam TEXT NOT NULL,
    target_cam TEXT NOT NULL,
    distance_km REAL NOT NULL,
    min_time_sec REAL NOT NULL,
    max_time_sec REAL NOT NULL,
    speed_limit_kmh REAL DEFAULT 50.0,
    FOREIGN KEY(source_cam) REFERENCES cameras(camera_id),
    FOREIGN KEY(target_cam) REFERENCES cameras(camera_id)
);

-- Real-Time Detections / Observations Table
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    frame_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    bbox_x1 REAL NOT NULL,
    bbox_y1 REAL NOT NULL,
    bbox_x2 REAL NOT NULL,
    bbox_y2 REAL NOT NULL,
    vehicle_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    estimated_speed REAL DEFAULT 0.0,
    color TEXT DEFAULT 'unknown',
    plate_text TEXT,
    plate_confidence REAL DEFAULT 0.0,
    embedding_json TEXT,
    FOREIGN KEY(camera_id) REFERENCES cameras(camera_id)
);

-- Global Re-ID & Identity Table
CREATE TABLE IF NOT EXISTS vehicle_identities (
    global_vehicle_id TEXT PRIMARY KEY,
    primary_plate TEXT,
    vehicle_class TEXT NOT NULL,
    color TEXT,
    make_model TEXT,
    embedding_json TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observation_count INTEGER DEFAULT 1
);

-- Cross-Camera Vehicle Journeys Table
CREATE TABLE IF NOT EXISTS journeys (
    journey_id TEXT PRIMARY KEY,
    global_vehicle_id TEXT NOT NULL,
    start_camera TEXT NOT NULL,
    end_camera TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    total_distance_km REAL DEFAULT 0.0,
    avg_speed_kmh REAL DEFAULT 0.0,
    trajectory_json TEXT NOT NULL,
    status TEXT DEFAULT 'COMPLETED',
    FOREIGN KEY(global_vehicle_id) REFERENCES vehicle_identities(global_vehicle_id)
);

-- Traffic Anomalies and Security Events Table
CREATE TABLE IF NOT EXISTS traffic_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL, -- CONGESTION, SPEEDING, WRONG_WAY, STOPPED_VEHICLE, WATCHLIST_HIT
    severity TEXT NOT NULL,   -- LOW, MEDIUM, HIGH, CRITICAL
    camera_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details_json TEXT NOT NULL,
    resolved INTEGER DEFAULT 0,
    FOREIGN KEY(camera_id) REFERENCES cameras(camera_id)
);

-- Security Watchlist Table
CREATE TABLE IF NOT EXISTS watchlist (
    plate_number TEXT PRIMARY KEY,
    vehicle_desc TEXT NOT NULL,
    reason TEXT NOT NULL,
    priority TEXT DEFAULT 'HIGH',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1
);

-- Audit Trail Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    user_role TEXT DEFAULT 'operator',
    query_or_event TEXT NOT NULL,
    details TEXT
);

-- Traffic Police Official E-Challans Table (Motor Vehicles Act 2019)
CREATE TABLE IF NOT EXISTS echallans (
    challan_no TEXT PRIMARY KEY,
    plate_number TEXT NOT NULL,
    violation_type TEXT NOT NULL,
    section_act TEXT NOT NULL,
    fine_amount INTEGER NOT NULL,
    camera_id TEXT NOT NULL,
    intersection TEXT NOT NULL,
    recorded_speed REAL DEFAULT 0.0,
    speed_limit REAL DEFAULT 50.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'PENDING_PAYMENT',
    officer_badge TEXT DEFAULT 'DEL-TP-7429',
    evidence_notes TEXT,
    FOREIGN KEY(camera_id) REFERENCES cameras(camera_id)
);

-- Emergency Green Corridor Clearance Table
CREATE TABLE IF NOT EXISTS green_corridors (
    corridor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    emergency_type TEXT NOT NULL, -- AMBULANCE, FIRE_BRIGADE, ORGAN_TRANSPLANT, VIP_CONVOY
    vehicle_plate TEXT,
    origin_cam TEXT NOT NULL,
    dest_cam TEXT NOT NULL,
    route_json TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, COMPLETED, CANCELLED
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority_level TEXT DEFAULT 'CRITICAL_LEVEL_1'
);

-- Police Control Room (PCR) Patrol Units Table
CREATE TABLE IF NOT EXISTS pcr_units (
    unit_id TEXT PRIMARY KEY,
    call_sign TEXT NOT NULL,
    officer_in_charge TEXT NOT NULL,
    current_junction TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    status TEXT DEFAULT 'ON_PATROL', -- ON_PATROL, STANDBY, DISPATCHED_INTERCEPT, BUSY
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for Fast Querying
CREATE INDEX IF NOT EXISTS idx_obs_cam_time ON observations(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_obs_plate ON observations(plate_text);
CREATE INDEX IF NOT EXISTS idx_journeys_veh ON journeys(global_vehicle_id);
CREATE INDEX IF NOT EXISTS idx_events_time ON traffic_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_challans_plate ON echallans(plate_number);
"""

