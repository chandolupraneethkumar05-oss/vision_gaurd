"""ANPR and Security Watchlist API routes."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from visionguard.database.db_manager import db
from visionguard.vision.anpr import IndianPlateValidator

router = APIRouter(prefix="/api/anpr", tags=["ANPR & Watchlist"])

class PlateValidationRequest(BaseModel):
    raw_text: str

class WatchlistCreateRequest(BaseModel):
    plate_number: str
    vehicle_desc: str
    reason: str
    priority: str = "HIGH"

@router.get("/observations")
def get_anpr_observations(limit: int = 50, camera_id: Optional[str] = None):
    """Retrieves recent license plate observations with recognition confidence."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        if camera_id:
            cursor.execute("""
                SELECT o.*, c.name as camera_name, c.intersection
                FROM observations o
                JOIN cameras c ON o.camera_id = c.camera_id
                WHERE o.camera_id = ? AND o.plate_text IS NOT NULL AND o.plate_text != ''
                ORDER BY o.id DESC LIMIT ?
            """, (camera_id, limit))
        else:
            cursor.execute("""
                SELECT o.*, c.name as camera_name, c.intersection
                FROM observations o
                JOIN cameras c ON o.camera_id = c.camera_id
                WHERE o.plate_text IS NOT NULL AND o.plate_text != ''
                ORDER BY o.id DESC LIMIT ?
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

@router.post("/validate")
def validate_indian_plate(req: PlateValidationRequest):
    """Validates raw text against standard Indian HSRP / BH / Commercial plate rules."""
    is_valid, formatted, category = IndianPlateValidator.validate_and_format(req.raw_text)
    return {
        "raw_text": req.raw_text,
        "is_valid_format": is_valid,
        "standardized_plate": formatted,
        "category": category
    }

@router.get("/watchlist")
def get_watchlist():
    """Returns active security watchlist entries."""
    return db.get_watchlist()

@router.post("/watchlist")
def add_to_watchlist(req: WatchlistCreateRequest):
    """Adds a target vehicle plate to active surveillance watchlist."""
    is_valid, formatted, _ = IndianPlateValidator.validate_and_format(req.plate_number)
    target_plate = formatted if is_valid else req.plate_number.upper()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO watchlist (plate_number, vehicle_desc, reason, priority, active)
            VALUES (?, ?, ?, ?, 1)
        """, (target_plate, req.vehicle_desc, req.reason, req.priority))
        conn.commit()

    db.add_audit_log("WATCHLIST_ADD", f"Added {target_plate} to watchlist: {req.reason}")
    return {"status": "SUCCESS", "plate_number": target_plate}

@router.delete("/watchlist/{plate_number}")
def remove_from_watchlist(plate_number: str):
    """Deactivates a plate from surveillance watchlist."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE watchlist SET active = 0 WHERE plate_number = ?", (plate_number,))
        conn.commit()

    db.add_audit_log("WATCHLIST_REMOVE", f"Deactivated {plate_number} from watchlist")
    return {"status": "DEACTIVATED", "plate_number": plate_number}
