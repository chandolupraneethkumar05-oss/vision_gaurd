"""FastAPI Application entrypoint for VisionGuard."""
import asyncio
import json
import random
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from visionguard.config import CORS_ORIGINS, BASE_DIR
from visionguard.database.db_manager import db
from visionguard.api.websocket_hub import ws_hub
from visionguard.api.routes import cameras, anpr, journeys, analytics, assistant, system
from visionguard.analytics.anomaly_detector import TrafficAnomalyDetector
from visionguard.association.journey_reconstructor import JourneyReconstructor

anomaly_detector = TrafficAnomalyDetector()
journey_reconstructor = JourneyReconstructor()

async def simulate_live_traffic_background():
    """Background task simulating periodic real-world vehicle detections and alerts."""
    plates_pool = [
        ("DL 01 AB 1234", "car", "white", 45.0),
        ("MH 12 CD 5678", "suv", "black", 72.0), # Speeding
        ("DL 1P B 8821", "bus", "green", 34.0),
        ("DL 1R C 3490", "auto_rickshaw", "yellow", 29.0),
        ("HR 26 DQ 7712", "motorcycle", "red", 58.0),
        ("UP 16 XY 9999", "car", "silver", 48.0),
        ("KA 05 MN 4321", "car", "red", 51.0),
        ("22 BH 5543 AB", "suv", "white", 46.0),
        ("DL 04 EF 9012", "car", "blue", 42.0)
    ]
    cameras_list = db.get_all_cameras()

    while True:
        try:
            await asyncio.sleep(5) # Emit new observation every 5 seconds
            if not cameras_list:
                cameras_list = db.get_all_cameras()
                continue

            target_cam = random.choice(cameras_list)
            plate_data = random.choice(plates_pool)
            plate_text, v_class, color, speed = plate_data
            
            # Slight random jitter
            actual_speed = round(speed + random.uniform(-4, 6), 1)
            frame_id = random.randint(100, 9999)
            track_id = random.randint(1, 50)

            obs_data = {
                "camera_id": target_cam["camera_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frame_id": frame_id,
                "track_id": track_id,
                "bbox_x1": random.randint(100, 300),
                "bbox_y1": random.randint(100, 200),
                "bbox_x2": random.randint(350, 500),
                "bbox_y2": random.randint(250, 350),
                "vehicle_class": v_class,
                "confidence": round(random.uniform(0.85, 0.98), 2),
                "estimated_speed": actual_speed,
                "color": color,
                "plate_text": plate_text,
                "plate_confidence": round(random.uniform(0.88, 0.99), 2),
                "embedding_json": None
            }

            obs_id = db.insert_observation(obs_data)
            obs_data["id"] = obs_id
            obs_data["camera_name"] = target_cam["name"]
            obs_data["intersection"] = target_cam["intersection"]

            # Update global vehicle identity
            veh_id = f"VEH-{plate_text.replace(' ', '')}"
            db.upsert_vehicle_identity({
                "global_vehicle_id": veh_id,
                "primary_plate": plate_text,
                "vehicle_class": v_class,
                "color": color
            })

            # Check for anomalies / alerts
            alerts = anomaly_detector.evaluate_observation(obs_data, target_cam)

            # Broadcast over WebSocket to live UI
            await ws_hub.broadcast({
                "type": "NEW_OBSERVATION",
                "data": obs_data,
                "alerts": alerts
            })

        except Exception as e:
            # Continue running resiliently
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed initial rich trajectory if needed
    _seed_initial_rich_trajectories()
    sim_task = asyncio.create_task(simulate_live_traffic_background())
    yield
    # Shutdown
    sim_task.cancel()

def _seed_initial_rich_trajectories():
    """Ensures at least two multi-camera journeys are pre-populated for demonstration."""
    existing_journeys = db.get_all_journeys(limit=5)
    if not existing_journeys:
        # Pre-seed journey for DL 01 AB 1234 across CAM-01 -> CAM-02 -> CAM-04 -> CAM-06
        veh_id = "VEH-DL01AB1234"
        now = datetime.now(timezone.utc)
        obs_seq = [
            {
                "camera_id": "CAM-01",
                "timestamp": (now - asyncio.to_thread.__defaults__ and (now)).isoformat() if False else (now).isoformat(),
                "frame_id": 120,
                "track_id": 14,
                "bbox_x1": 180, "bbox_y1": 90, "bbox_x2": 240, "bbox_y2": 160,
                "vehicle_class": "suv", "confidence": 0.96, "estimated_speed": 48.0,
                "color": "white", "plate_text": "DL 01 AB 1234", "plate_confidence": 0.98
            },
            {
                "camera_id": "CAM-02",
                "timestamp": now.isoformat(),
                "frame_id": 180,
                "track_id": 22,
                "bbox_x1": 200, "bbox_y1": 110, "bbox_x2": 260, "bbox_y2": 180,
                "vehicle_class": "suv", "confidence": 0.95, "estimated_speed": 46.5,
                "color": "white", "plate_text": "DL 01 AB 1234", "plate_confidence": 0.97
            },
            {
                "camera_id": "CAM-04",
                "timestamp": now.isoformat(),
                "frame_id": 240,
                "track_id": 31,
                "bbox_x1": 220, "bbox_y1": 120, "bbox_x2": 280, "bbox_y2": 190,
                "vehicle_class": "suv", "confidence": 0.94, "estimated_speed": 44.0,
                "color": "white", "plate_text": "DL 01 AB 1234", "plate_confidence": 0.96
            }
        ]
        for o in obs_seq:
            db.insert_observation(o)
        db.upsert_vehicle_identity({
            "global_vehicle_id": veh_id,
            "primary_plate": "DL 01 AB 1234",
            "vehicle_class": "suv",
            "color": "white"
        })
        journey_reconstructor.reconstruct_from_observations(veh_id, obs_seq)

app = FastAPI(
    title="VisionGuard: AI Urban Traffic Intelligence Platform",
    description="Multi-Camera ANPR, Cross-Camera Vehicle Re-ID, and Spatial Traffic Analytics Engine.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(cameras.router)
app.include_router(anpr.router)
app.include_router(journeys.router)
app.include_router(analytics.router)
app.include_router(assistant.router)
app.include_router(system.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_hub.connect(websocket)
    try:
        while True:
            # Keep connection open; receive heartbeats or client commands
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception:
        ws_hub.disconnect(websocket)

@app.get("/api/status")
def api_status():
    return {
        "platform": "VisionGuard AI Urban Traffic Intelligence",
        "version": "1.0.0",
        "docs_url": "/docs",
        "status": "OPERATIONAL"
    }

# Mount Frontend UI if built, otherwise provide API status at root
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "platform": "VisionGuard AI Urban Traffic Intelligence",
            "version": "1.0.0",
            "docs_url": "/docs",
            "status": "OPERATIONAL"
        }


