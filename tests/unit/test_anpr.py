"""Unit tests for Indian ANPR format validation and temporal voting."""
import numpy as np
from visionguard.vision.anpr import IndianPlateValidator, PlateVotingBuffer, ANPREngine

def test_indian_plate_validator_standard():
    valid, formatted, cat = IndianPlateValidator.validate_and_format("DL01AB1234")
    assert valid is True
    assert formatted == "DL 01 AB 1234"
    assert cat == "STANDARD_HSRP"

def test_indian_plate_validator_bharat():
    valid, formatted, cat = IndianPlateValidator.validate_and_format("22BH1234AA")
    assert valid is True
    assert formatted == "22 BH 1234 AA"
    assert cat == "BHARAT_SERIES"

def test_indian_plate_validator_invalid():
    valid, formatted, cat = IndianPlateValidator.validate_and_format("INVALID123XYZ")
    assert valid is False

def test_plate_voting_buffer():
    buffer = PlateVotingBuffer(window_size=5)
    # Add noisy readings for track_id 1
    buffer.add_reading(1, "DL 01 AB 1234", 0.95)
    buffer.add_reading(1, "DL 01 AB 1234", 0.90)
    buffer.add_reading(1, "DL 01 A8 1234", 0.60) # OCR noise
    buffer.add_reading(1, "DL 01 AB 1234", 0.92)

    consensus = buffer.get_consensus(1)
    assert consensus is not None
    plate, conf = consensus
    assert plate == "DL01AB1234"
    assert conf > 0.85
