"""Bayesian Multi-Modal Association Matcher for Cross-Camera Vehicle Tracking."""
import re
from typing import Dict, Any, Tuple, Optional
from visionguard.config import WEIGHT_PLATE, WEIGHT_APPEARANCE, WEIGHT_SPATIO_TEMPORAL
from visionguard.association.camera_graph import CameraGraph
from visionguard.vision.reid import VehicleReIDExtractor

def levenshtein_similarity(s1: str, s2: str) -> float:
    """Computes normalized string edit similarity in range [0.0, 1.0]."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.upper().replace(" ", ""), s2.upper().replace(" ", "")
    if s1 == s2:
        return 1.0
    
    len1, len2 = len(s1), len(s2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    dist = dp[len1][len2]
    max_len = max(len1, len2)
    return max(0.0, 1.0 - (dist / float(max_len)))

class BayesianCrossCameraMatcher:
    """
    Fuses License Plate Match, Visual Appearance Re-ID, and Spatio-Temporal
    Feasibility to resolve vehicle identity across non-overlapping cameras.
    """

    def __init__(self, camera_graph: Optional[CameraGraph] = None):
        self.camera_graph = camera_graph or CameraGraph()
        self.reid_extractor = VehicleReIDExtractor()

    def compute_match_score(
        self,
        obs1: Dict[str, Any],
        obs2: Dict[str, Any],
        delta_seconds: float
    ) -> Dict[str, Any]:
        """
        Fuses three independent evidence sources:
        1. Plate Match Score (Exact match = 1.0, 1-char OCR error = ~0.88, no match = 0.0)
        2. Appearance Re-ID Cosine Similarity
        3. Spatio-Temporal Transition Feasibility
        """
        cam1 = obs1.get("camera_id")
        cam2 = obs2.get("camera_id")
        plate1 = obs1.get("plate_text")
        plate2 = obs2.get("plate_text")

        # 1. Plate Evidence
        if plate1 and plate2:
            plate_score = levenshtein_similarity(plate1, plate2)
            has_plate_evidence = True
        else:
            plate_score = 0.5  # Neutral prior if plate is occluded
            has_plate_evidence = False

        # 2. Appearance Evidence
        emb1 = obs1.get("embedding")
        emb2 = obs2.get("embedding")
        if emb1 is not None and emb2 is not None:
            appearance_score = self.reid_extractor.compute_cosine_similarity(emb1, emb2)
        else:
            # Fallback to class and color matching
            class_match = 1.0 if obs1.get("vehicle_class") == obs2.get("vehicle_class") else 0.2
            color_match = 1.0 if obs1.get("color") == obs2.get("color") else 0.4
            appearance_score = 0.6 * class_match + 0.4 * color_match

        # 3. Spatio-Temporal Evidence
        st_score, st_reason = self.camera_graph.evaluate_spatio_temporal_feasibility(
            cam1, cam2, delta_seconds
        )

        # Dynamic weight adjustment based on available evidence
        if has_plate_evidence:
            w_p, w_a, w_st = WEIGHT_PLATE, WEIGHT_APPEARANCE, WEIGHT_SPATIO_TEMPORAL
        else:
            # If plate is occluded, weight appearance and spatial physics higher
            w_p, w_a, w_st = 0.10, 0.55, 0.35

        # If spatial constraints are physically impossible (teleportation), hard veto!
        if st_score == 0.0:
            total_score = 0.0
            is_match = False
            uncertainty = "VETOED_BY_PHYSICS"
        else:
            total_score = (w_p * plate_score) + (w_a * appearance_score) + (w_st * st_score)
            is_match = total_score >= 0.72
            uncertainty = "LOW" if total_score > 0.85 else ("MEDIUM" if total_score > 0.65 else "HIGH")

        return {
            "is_match": is_match,
            "overall_score": round(total_score, 4),
            "plate_score": round(plate_score, 3),
            "appearance_score": round(appearance_score, 3),
            "spatio_temporal_score": round(st_score, 3),
            "spatio_temporal_reason": st_reason,
            "uncertainty": uncertainty
        }
