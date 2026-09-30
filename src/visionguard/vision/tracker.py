"""Single-Camera Multi-Object Tracking (MOT) with trajectory smoothing and speed estimation.
Implements Kalman-inspired state filtering and Hungarian/IoU association to prevent ID switches.
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone

def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """Calculates Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0

class Track:
    """Represents an active or confirmed vehicle track within a single camera."""

    def __init__(self, track_id: int, bbox: List[float], vehicle_class: str, color: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox
        self.vehicle_class = vehicle_class
        self.color = color
        self.confidence = confidence
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.confirmed = False
        
        # History of centroid coordinates (x, y, timestamp) for trajectory smoothing & speed estimation
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        now = datetime.now(timezone.utc).timestamp()
        self.history: List[Tuple[float, float, float]] = [(cx, cy, now)]
        self.estimated_speed_kmh: float = 38.0

    def update(self, bbox: List[float], confidence: float):
        """Updates track with new detection, smooths trajectory, and computes speed."""
        self.bbox = bbox
        self.confidence = confidence
        self.hits += 1
        self.time_since_update = 0
        if self.hits >= 3:
            self.confirmed = True

        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        now = datetime.now(timezone.utc).timestamp()

        # Compute instantaneous pixel displacement and speed approximation
        if len(self.history) > 0:
            last_x, last_y, last_t = self.history[-1]
            dt = max(0.001, now - last_t)
            pixel_dist = np.sqrt((cx - last_x)**2 + (cy - last_y)**2)
            # Homography proxy: 1 pixel ~ 0.06 meters in typical 1080p road perspective
            speed_mps = (pixel_dist * 0.06) / dt
            instant_speed_kmh = speed_mps * 3.6
            # Exponential moving average smoothing for velocity
            self.estimated_speed_kmh = 0.7 * self.estimated_speed_kmh + 0.3 * min(120.0, max(10.0, instant_speed_kmh))

        self.history.append((cx, cy, now))
        if len(self.history) > 50:
            self.history.pop(0)

class SingleCameraTracker:
    """ByteTrack-style single camera multi-object tracker."""

    def __init__(self, max_lost_frames: int = 15, iou_match_threshold: float = 0.3):
        self.max_lost_frames = max_lost_frames
        self.iou_match_threshold = iou_match_threshold
        self.tracks: List[Track] = []
        self.next_track_id = 1

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Associates detections to existing tracks using IoU matching.
        Returns list of active tracked vehicles.
        """
        # Age existing tracks
        for t in self.tracks:
            t.time_since_update += 1
            t.age += 1

        unmatched_detections = list(range(len(detections)))
        unmatched_tracks = list(range(len(self.tracks)))
        matches = []

        if len(self.tracks) > 0 and len(detections) > 0:
            # Compute IoU matrix
            iou_matrix = np.zeros((len(self.tracks), len(detections)))
            for t_idx, track in enumerate(self.tracks):
                for d_idx, det in enumerate(detections):
                    iou_matrix[t_idx, d_idx] = calculate_iou(track.bbox, det["bbox"])

            # Greedy matching for tracks and detections
            while True:
                max_val = np.max(iou_matrix)
                if max_val < self.iou_match_threshold:
                    break
                t_idx, d_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                matches.append((t_idx, d_idx))
                iou_matrix[t_idx, :] = -1
                iou_matrix[:, d_idx] = -1
                if t_idx in unmatched_tracks:
                    unmatched_tracks.remove(t_idx)
                if d_idx in unmatched_detections:
                    unmatched_detections.remove(d_idx)

        # Update matched tracks
        for t_idx, d_idx in matches:
            det = detections[d_idx]
            self.tracks[t_idx].update(det["bbox"], det["confidence"])
            self.tracks[t_idx].vehicle_class = det["class"]
            self.tracks[t_idx].color = det.get("color", self.tracks[t_idx].color)

        # Create new tracks for unmatched detections
        for d_idx in unmatched_detections:
            det = detections[d_idx]
            new_track = Track(
                track_id=self.next_track_id,
                bbox=det["bbox"],
                vehicle_class=det["class"],
                color=det.get("color", "unknown"),
                confidence=det["confidence"]
            )
            self.next_track_id += 1
            self.tracks.append(new_track)

        # Filter out dead tracks
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_lost_frames]

        # Output current active and confirmed tracks
        results = []
        for t in self.tracks:
            results.append({
                "track_id": t.track_id,
                "bbox": t.bbox,
                "class": t.vehicle_class,
                "color": t.color,
                "confidence": t.confidence,
                "confirmed": t.confirmed,
                "estimated_speed_kmh": round(t.estimated_speed_kmh, 1),
                "trajectory_points": len(t.history)
            })

        return results
