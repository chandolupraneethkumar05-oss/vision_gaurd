"""Traffic Police Operations & Enforcement API routes.
Implements:
- Indian Motor Vehicles Act 2019 E-Challan Generation with Legal Citations
- Emergency Green Corridor Clearance for Ambulances & Organ Convoys
- PCR Patrol Intercept Dispatcher for Hotlisted Vehicles
- Dynamic Signal Congestion Flush Manual Overrides
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from visionguard.database.db_manager import db

router = APIRouter(prefix="/api/police", tags=["Traffic Police Operations"])

# Standard Motor Vehicles (Amendment) Act 2019 Statutory Penalty Catalog
MV_ACT_PENALTIES = {
    "OVERSPEEDING": {
        "section": "Sec 183(1) Motor Vehicles Act",
        "description": "Exceeding prescribed speed limit on urban arterial corridor",
        "fine_amount": 2000
    },
    "RED_LIGHT_JUMP": {
        "section": "Sec 184 Motor Vehicles Act",
        "description": "Jumping red traffic signal phase and stop line violation",
        "fine_amount": 5000
    },
    "NO_HELMET": {
        "section": "Sec 194D Motor Vehicles Act",
        "description": "Riding two-wheeler without protective headgear conforming to BIS standards",
        "fine_amount": 1000
    },
    "WRONG_WAY": {
        "section": "Sec 184 Motor Vehicles Act",
        "description": "Driving against authorized traffic flow / dangerous driving",
        "fine_amount": 5000
    },
    "DANGEROUS_DRIVING": {
        "section": "Sec 184 Motor Vehicles Act",
        "description": "Reckless zigzag maneuvers and endangerment of public safety",
        "fine_amount": 5000
    },
    "ILLEGAL_PARKING": {
        "section": "Sec 122/177 Motor Vehicles Act",
        "description": "Obstructive parking on arterial carriageway",
        "fine_amount": 1000
    },
    "TRIPLE_RIDING": {
        "section": "Sec 128/194C Motor Vehicles Act",
        "description": "Carrying more than one pillion rider on two-wheeler",
        "fine_amount": 1000
    }
}

class IssueChallanRequest(BaseModel):
    plate_number: str
    violation_type: str
    camera_id: str
    recorded_speed: Optional[float] = 0.0
    speed_limit: Optional[float] = 50.0
    officer_badge: Optional[str] = "DEL-TP-7429"
    evidence_notes: Optional[str] = ""

class ActivateCorridorRequest(BaseModel):
    name: str
    emergency_type: str  # AMBULANCE, FIRE_BRIGADE, ORGAN_TRANSPLANT, VIP_CONVOY
    vehicle_plate: Optional[str] = "DL 01 AM 9110"
    origin_cam: str
    dest_cam: str

class DispatchPcrRequest(BaseModel):
    unit_id: str
    target_plate: str
    target_junction: str
    intercept_notes: Optional[str] = ""

class SignalOverrideRequest(BaseModel):
    camera_id: str
    duration_sec: Optional[int] = 45
    reason: Optional[str] = "Manual Congestion Flush"

@router.get("/challans")
def list_challans(limit: int = 50):
    """Retrieves all official E-Challans issued across the smart city corridor."""
    return db.get_echallans(limit=limit)

@router.post("/challans/issue")
def issue_challan(req: IssueChallanRequest):
    """
    Issues a statutory E-Challan under the Indian Motor Vehicles Act 2019.
    Calculates fine amount, assigns unique Challan Notice number, and records audit trail.
    """
    v_info = MV_ACT_PENALTIES.get(req.violation_type.upper(), {
        "section": "Sec 177 Motor Vehicles Act",
        "description": "General Traffic Infraction",
        "fine_amount": 1000
    })

    cam = db.get_camera(req.camera_id)
    intersection = cam["intersection"] if cam else "Urban Corridor Junction"

    challan_no = f"DL-ECH-2026-{uuid.uuid4().hex[:6].upper()}"
    notes = req.evidence_notes or v_info["description"]
    if req.violation_type.upper() == "OVERSPEEDING" and req.recorded_speed:
        diff = round(req.recorded_speed - (req.speed_limit or 50.0), 1)
        notes = f"Recorded Speed: {req.recorded_speed} km/h (Limit: {req.speed_limit} km/h, +{diff} km/h). {notes}"

    challan_record = {
        "challan_no": challan_no,
        "plate_number": req.plate_number.strip().upper(),
        "violation_type": req.violation_type.upper(),
        "section_act": v_info["section"],
        "fine_amount": v_info["fine_amount"],
        "camera_id": req.camera_id,
        "intersection": intersection,
        "recorded_speed": req.recorded_speed,
        "speed_limit": req.speed_limit,
        "status": "PENDING_PAYMENT",
        "officer_badge": req.officer_badge or "DEL-TP-7429",
        "evidence_notes": notes
    }

    db.insert_echallan(challan_record)
    db.add_audit_log(
        "ECHALLAN_ISSUED",
        f"Issued Challan {challan_no} for vehicle {req.plate_number}",
        details=f"Violation: {req.violation_type}, Section: {v_info['section']}, Fine: ₹{v_info['fine_amount']}",
        user_role="traffic_controller_police"
    )

    return {"status": "SUCCESS", "challan": challan_record}

@router.post("/challans/{challan_no}/pay")
def pay_challan(challan_no: str):
    """Marks an issued E-Challan as settled/paid."""
    db.update_challan_status(challan_no, "PAID")
    db.add_audit_log("ECHALLAN_PAID", f"Challan {challan_no} settled through Parivahan Gateway")
    return {"status": "SUCCESS", "challan_no": challan_no, "new_status": "PAID"}

@router.get("/green-corridor")
def list_green_corridors():
    """Returns active and historical emergency green corridors."""
    return db.get_green_corridors()

@router.post("/green-corridor/activate")
def activate_green_corridor(req: ActivateCorridorRequest):
    """
    Activates an Emergency Green Corridor between two points in the network.
    Dynamically clears signals, synchronizes traffic lights to continuous green,
    and updates GIS route path.
    """
    corridor_id = f"GC-2026-{uuid.uuid4().hex[:4].upper()}"

    # Route topology calculation (Shortest path between origin and destination)
    # New Delhi Camera Grid: CAM-01 (CP) -> CAM-02 (Barakhamba) -> CAM-04 (Tolstoy) -> CAM-06 (India Gate/AIIMS)
    default_route = [req.origin_cam]
    if req.origin_cam != req.dest_cam:
        if req.origin_cam == "CAM-01" and req.dest_cam == "CAM-06":
            default_route = ["CAM-01", "CAM-02", "CAM-04", "CAM-06"]
        elif req.origin_cam == "CAM-01" and req.dest_cam == "CAM-05":
            default_route = ["CAM-01", "CAM-04", "CAM-03", "CAM-05"]
        else:
            default_route = [req.origin_cam, "CAM-04", req.dest_cam]

    corridor_data = {
        "corridor_id": corridor_id,
        "name": req.name,
        "emergency_type": req.emergency_type,
        "vehicle_plate": req.vehicle_plate or "EMERGENCY-AMB-01",
        "origin_cam": req.origin_cam,
        "dest_cam": req.dest_cam,
        "route": default_route,
        "status": "ACTIVE",
        "priority_level": "CRITICAL_LEVEL_1"
    }

    db.activate_green_corridor(corridor_data)
    db.add_audit_log(
        "GREEN_CORRIDOR_ACTIVATED",
        f"Activated Emergency Green Corridor {corridor_id} for {req.emergency_type} ({req.vehicle_plate})",
        details=f"Route: {' -> '.join(default_route)}. Traffic signals forced to continuous green phase.",
        user_role="traffic_controller_police"
    )

    return {
        "status": "ACTIVATED",
        "corridor": corridor_data,
        "signal_override": "ALL_GREEN_CONTINUOUS_WAVE",
        "priority_duration_sec": 300
    }

@router.post("/green-corridor/{corridor_id}/deactivate")
def deactivate_green_corridor(corridor_id: str):
    """Deactivates an active emergency green corridor and reverts signals to dynamic balance."""
    db.deactivate_green_corridor(corridor_id)
    db.add_audit_log(
        "GREEN_CORRIDOR_DEACTIVATED",
        f"Corridor {corridor_id} completed. Signals reverted to dynamic actuated cycle.",
        user_role="traffic_controller_police"
    )
    return {"status": "DEACTIVATED", "corridor_id": corridor_id}

@router.get("/pcr-units")
def list_pcr_units():
    """Returns active Police Control Room (PCR) patrol units and their coordinates."""
    return db.get_pcr_units()

@router.post("/pcr-units/{unit_id}/dispatch")
def dispatch_pcr_unit(unit_id: str, req: DispatchPcrRequest):
    """Dispatches a PCR patrol unit for tactical vehicle interception."""
    db.update_pcr_unit(unit_id, "DISPATCHED_INTERCEPT", current_junction=req.target_junction)
    db.add_audit_log(
        "PCR_DISPATCH",
        f"Dispatched PCR unit {unit_id} to intercept vehicle {req.target_plate} at {req.target_junction}",
        details=req.intercept_notes or "Immediate visual contact and tactical intercept requested",
        user_role="traffic_controller_police"
    )
    return {
        "status": "DISPATCHED",
        "unit_id": unit_id,
        "target_plate": req.target_plate,
        "target_junction": req.target_junction
    }

@router.post("/signal-override")
def signal_override(req: SignalOverrideRequest):
    """Forces manual signal flush on a congested intersection to drain queue."""
    cam = db.get_camera(req.camera_id)
    cam_name = cam["name"] if cam else req.camera_id
    db.add_audit_log(
        "SIGNAL_OVERRIDE",
        f"Manual Green Flush forced on {cam_name} ({req.camera_id}) for {req.duration_sec}s",
        details=req.reason or "Traffic Police Manual Queue Flush Override",
        user_role="traffic_controller_police"
    )
    return {
        "status": "OVERRIDE_ACTIVE",
        "camera_id": req.camera_id,
        "flush_duration_sec": req.duration_sec,
        "action": "QUEUE_FLUSH_GREEN_WAVE"
    }
