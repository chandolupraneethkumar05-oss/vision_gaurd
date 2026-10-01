"""Integration tests for Traffic Police Operations and E-Challan routes."""
import pytest
from fastapi.testclient import TestClient
from visionguard.api.app import app

client = TestClient(app)

def test_list_and_issue_echallan():
    # 1. List challans
    res = client.get("/api/police/challans")
    assert res.status_code == 200
    challans = res.json()
    assert isinstance(challans, list)

    # 2. Issue a new statutory E-Challan
    payload = {
        "plate_number": "DL 01 TR 9988",
        "violation_type": "OVERSPEEDING",
        "camera_id": "CAM-01",
        "recorded_speed": 76.5,
        "speed_limit": 50.0,
        "officer_badge": "DEL-TP-7429",
        "evidence_notes": "Automated radar detection test"
    }
    issue_res = client.post("/api/police/challans/issue", json=payload)
    assert issue_res.status_code == 200
    data = issue_res.json()
    assert data["status"] == "SUCCESS"
    challan = data["challan"]
    assert challan["fine_amount"] == 2000
    assert "Sec 183" in challan["section_act"]
    challan_no = challan["challan_no"]

    # 3. Pay the challan
    pay_res = client.post(f"/api/police/challans/{challan_no}/pay")
    assert pay_res.status_code == 200
    assert pay_res.json()["new_status"] == "PAID"

def test_green_corridor_lifecycle():
    # 1. List corridors
    list_res = client.get("/api/police/green-corridor")
    assert list_res.status_code == 200
    corridors = list_res.json()
    assert isinstance(corridors, list)

    # 2. Activate emergency corridor
    payload = {
        "name": "Apollo Emergency Life Support Corridor",
        "emergency_type": "AMBULANCE",
        "vehicle_plate": "DL 01 AM 9999",
        "origin_cam": "CAM-01",
        "dest_cam": "CAM-06"
    }
    act_res = client.post("/api/police/green-corridor/activate", json=payload)
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["status"] == "ACTIVATED"
    corridor_id = act_data["corridor"]["corridor_id"]
    assert act_data["corridor"]["route"] == ["CAM-01", "CAM-02", "CAM-04", "CAM-06"]

    # 3. Deactivate corridor
    deact_res = client.post(f"/api/police/green-corridor/{corridor_id}/deactivate")
    assert deact_res.status_code == 200
    assert deact_res.json()["status"] == "DEACTIVATED"

def test_pcr_dispatch_and_signal_override():
    # 1. Get PCR units
    pcr_res = client.get("/api/police/pcr-units")
    assert pcr_res.status_code == 200
    units = pcr_res.json()
    assert len(units) >= 1
    unit_id = units[0]["unit_id"]

    # 2. Dispatch PCR unit
    dispatch_res = client.post(f"/api/police/pcr-units/{unit_id}/dispatch", json={
        "unit_id": unit_id,
        "target_plate": "DL 01 AB 1234",
        "target_junction": "CAM-02",
        "intercept_notes": "Armed robbery suspect heading East"
    })
    assert dispatch_res.status_code == 200
    assert dispatch_res.json()["status"] == "DISPATCHED"

    # 3. Force manual signal override
    override_res = client.post("/api/police/signal-override", json={
        "camera_id": "CAM-01",
        "duration_sec": 45,
        "reason": "Clear gridlock queue at Barakhamba"
    })
    assert override_res.status_code == 200
    assert override_res.json()["status"] == "OVERRIDE_ACTIVE"
