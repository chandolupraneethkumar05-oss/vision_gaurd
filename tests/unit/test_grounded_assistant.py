"""Unit tests for Grounded Assistant."""
from visionguard.query.grounded_assistant import GroundedTrafficAssistant

def test_grounded_assistant_general():
    assistant = GroundedTrafficAssistant()
    res = assistant.process_query("What is the system overview?")
    assert res["grounded"] is True
    assert "urban camera junctions" in res["answer"]
    assert len(res["citations"]) > 0

def test_grounded_assistant_watchlist():
    assistant = GroundedTrafficAssistant()
    res = assistant.process_query("How many vehicles are in the watchlist?")
    assert res["grounded"] is True
    assert "watchlist" in res["answer"].lower()
