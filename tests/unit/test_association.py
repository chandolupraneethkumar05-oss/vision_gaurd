"""Unit tests for Camera Graph and Bayesian Association Matcher."""
from visionguard.association.camera_graph import CameraGraph
from visionguard.association.bayesian_matcher import BayesianCrossCameraMatcher, levenshtein_similarity

def test_camera_graph_spatio_temporal_veto():
    cg = CameraGraph()
    # Distance between CAM-01 and CAM-02 is ~0.75km, min expected time is 40 seconds.
    # If delta time is 5 seconds (teleportation!), it must be vetoed!
    score, reason = cg.evaluate_spatio_temporal_feasibility("CAM-01", "CAM-02", 5.0)
    assert score == 0.0
    assert "PHYSICALLY_IMPOSSIBLE_SPEED" in reason

def test_camera_graph_optimal_window():
    cg = CameraGraph()
    # Transit in 80 seconds is within optimal window (40-300 sec)
    score, reason = cg.evaluate_spatio_temporal_feasibility("CAM-01", "CAM-02", 80.0)
    assert score >= 0.65
    assert reason == "OPTIMAL_TRAVEL_WINDOW"

def test_levenshtein_similarity():
    assert levenshtein_similarity("DL 01 AB 1234", "DL 01 AB 1234") == 1.0
    # 1 character typo
    sim = levenshtein_similarity("DL 01 AB 1234", "DL 01 A8 1234")
    assert sim > 0.85
