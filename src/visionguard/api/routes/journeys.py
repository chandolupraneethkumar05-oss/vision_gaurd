"""Cross-Camera Vehicle Journeys and Trajectory API routes."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from visionguard.database.db_manager import db
from visionguard.association.journey_reconstructor import JourneyReconstructor

router = APIRouter(prefix="/api/journeys", tags=["Journeys & Trajectories"])
reconstructor = JourneyReconstructor()

@router.get("", response_model=List[Dict[str, Any]])
def list_journeys(limit: int = 50):
    """Returns reconstructed cross-camera vehicle journeys with trajectory waypoints."""
    return db.get_all_journeys(limit=limit)

@router.get("/vehicle/{vehicle_id}")
def get_vehicle_journeys(vehicle_id: str):
    """Retrieves all historical journeys recorded for a specific vehicle identity."""
    journeys = db.get_journeys_by_vehicle(vehicle_id)
    return journeys

@router.get("/{journey_id}")
def get_journey_detail(journey_id: str):
    """Retrieves full trajectory waypoints, corridor speeds, and camera path for a journey."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM journeys WHERE journey_id = ?", (journey_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        j = dict(row)
        import json
        j["trajectory"] = json.loads(j["trajectory_json"])
        return j

class JourneySearchQuery(BaseModel):
    plate: Optional[str] = None
    vehicle_class: Optional[str] = None
    color: Optional[str] = None

@router.post("/search")
def search_journeys(query: JourneySearchQuery):
    """Searches journeys matching license plate, vehicle class, or body color."""
    all_journeys = db.get_all_journeys(limit=100)
    filtered = []
    for j in all_journeys:
        match = True
        if query.plate:
            clean_q = query.plate.upper().replace(" ", "")
            primary = (j.get("primary_plate") or "").upper().replace(" ", "")
            if clean_q not in primary:
                match = False
        if query.vehicle_class and query.vehicle_class.lower() != (j.get("vehicle_class") or "").lower():
            match = False
        if query.color and query.color.lower() != (j.get("color") or "").lower():
            match = False
        if match:
            filtered.append(j)

    return filtered
