"""Traffic Intelligence and Analytics API routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from visionguard.database.db_manager import db
from visionguard.analytics.traffic_engine import TrafficAnalyticsEngine
from visionguard.analytics.od_matrix import OriginDestinationAnalyzer

router = APIRouter(prefix="/api/analytics", tags=["Traffic Analytics"])
analytics_engine = TrafficAnalyticsEngine()

@router.get("/network")
def get_network_analytics():
    """Returns network-wide traffic analytics, hourly volume trends, and Level of Service."""
    return analytics_engine.get_network_overview()

@router.get("/od-matrix")
def get_origin_destination_matrix():
    """Returns the Origin-Destination trip distribution matrix across smart junctions."""
    return OriginDestinationAnalyzer.compute_matrix()

@router.get("/events")
def get_traffic_events(limit: int = 50, unresolved_only: bool = False):
    """Retrieves real-time traffic anomalies, speeding violations, and watchlist alerts."""
    return db.get_traffic_events(limit=limit, unresolved_only=unresolved_only)

@router.post("/events/{event_id}/resolve")
def resolve_event(event_id: str):
    """Marks a traffic anomaly or security alert as addressed and resolved."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE traffic_events SET resolved = 1 WHERE event_id = ?", (event_id,))
        conn.commit()
    
    db.add_audit_log("EVENT_RESOLVE", f"Resolved incident {event_id}")
    return {"status": "RESOLVED", "event_id": event_id}
