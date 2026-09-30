"""Configuration and constants for VisionGuard platform."""
import os
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DB_PATH = DATA_DIR / "visionguard.db"

# API & Server Configuration
API_HOST = os.getenv("VG_HOST", "0.0.0.0")
API_PORT = int(os.getenv("VG_PORT", "8000"))
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"
]

# Supported Vehicle Classes
VEHICLE_CLASSES = ["car", "suv", "motorcycle", "auto_rickshaw", "bus", "truck"]

# Vehicle Colors for Re-ID and Filtering
VEHICLE_COLORS = ["white", "black", "silver", "gray", "red", "blue", "yellow", "green", "brown"]

# ANPR: Valid Indian State & UT Codes
INDIAN_STATE_CODES = [
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN", "GA",
    "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML",
    "MN", "MP", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR",
    "TS", "UK", "UP", "WB", "BH"  # BH = Bharat Series
]

# Tracking & Association Weights (Bayesian Fusion)
WEIGHT_PLATE = 0.45
WEIGHT_APPEARANCE = 0.35
WEIGHT_SPATIO_TEMPORAL = 0.20

# City Road Network Defaults (Lat/Lon for Smart City Camera Grid, e.g. New Delhi Urban Hub)
DEFAULT_CAMERAS = [
    {
        "camera_id": "CAM-01",
        "name": "Connaught Outer Radial 1",
        "latitude": 28.6328,
        "longitude": 77.2197,
        "intersection": "Barakhamba Junction",
        "direction": "Northbound",
        "road_segment": "Radial-1",
        "speed_limit_kmh": 50.0,
        "fps": 30,
        "resolution": "1920x1080",
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-02",
        "name": "Barakhamba Metro Crossing",
        "latitude": 28.6295,
        "longitude": 77.2260,
        "intersection": "Barakhamba Road",
        "direction": "Eastbound",
        "road_segment": "Radial-1-Ext",
        "speed_limit_kmh": 50.0,
        "fps": 30,
        "resolution": "1920x1080",
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-03",
        "name": "Janpath Central Boulevard",
        "latitude": 28.6234,
        "longitude": 77.2185,
        "intersection": "Janpath Intersection",
        "direction": "Southbound",
        "road_segment": "Janpath-Corridor",
        "speed_limit_kmh": 60.0,
        "fps": 30,
        "resolution": "1920x1080",
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-04",
        "name": "Tolstoy Marg Plaza",
        "latitude": 28.6268,
        "longitude": 77.2223,
        "intersection": "Tolstoy Crossing",
        "direction": "Westbound",
        "road_segment": "Tolstoy-Way",
        "speed_limit_kmh": 45.0,
        "fps": 30,
        "resolution": "1920x1080",
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-05",
        "name": "Sansad Marg Gate",
        "latitude": 28.6201,
        "longitude": 77.2112,
        "intersection": "Sansad Marg Entry",
        "direction": "Southwest",
        "road_segment": "Sansad-Express",
        "speed_limit_kmh": 50.0,
        "fps": 30,
        "resolution": "1920x1080",
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-06",
        "name": "India Gate C-Hexagon North",
        "latitude": 28.6142,
        "longitude": 77.2301,
        "intersection": "C-Hexagon Roundabout",
        "direction": "Southeast",
        "road_segment": "Hexagon-Ring",
        "speed_limit_kmh": 60.0,
        "fps": 30,
        "resolution": "1920x1080",
        "status": "ONLINE"
    }
]

# Road Network Graph Edges: (Source, Target, Distance in km, Typical Travel Time in seconds)
CAMERA_GRAPH_EDGES = [
    {"source": "CAM-01", "target": "CAM-02", "distance_km": 0.75, "min_time_sec": 40, "max_time_sec": 300},
    {"source": "CAM-02", "target": "CAM-04", "distance_km": 0.55, "min_time_sec": 30, "max_time_sec": 240},
    {"source": "CAM-01", "target": "CAM-04", "distance_km": 0.80, "min_time_sec": 45, "max_time_sec": 320},
    {"source": "CAM-04", "target": "CAM-03", "distance_km": 0.65, "min_time_sec": 35, "max_time_sec": 270},
    {"source": "CAM-03", "target": "CAM-05", "distance_km": 0.90, "min_time_sec": 50, "max_time_sec": 360},
    {"source": "CAM-04", "target": "CAM-06", "distance_km": 1.60, "min_time_sec": 90, "max_time_sec": 600},
    {"source": "CAM-03", "target": "CAM-06", "distance_km": 1.40, "min_time_sec": 80, "max_time_sec": 540}
]
