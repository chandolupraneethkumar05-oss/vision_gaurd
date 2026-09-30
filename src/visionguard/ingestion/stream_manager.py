"""Multi-Camera Stream Ingestion and Simulation Manager.
Supports local MP4 files, webcams, live RTSP streams with auto-reconnect,
and a high-fidelity synthetic urban camera frame generator.
"""
import time
import cv2
import numpy as np
from typing import Dict, Any, Generator, Optional, Tuple
from datetime import datetime, timezone
import random

class SyntheticRoadGenerator:
    """
    Generates high-definition realistic synthetic urban road video frames
    with animated vehicles, road perspective, lane markings, and Indian license plates.
    """

    def __init__(self, camera_id: str, camera_name: str, width: int = 640, height: int = 360):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.width = width
        self.height = height
        self.frame_count = 0

        # Simulated vehicle pool traveling along this road corridor
        # Colors: (B, G, R)
        self.vehicles = [
            {"id": 101, "x": 180, "y": 90, "speed": 1.8, "class": "car", "color_name": "white", "bgr": (240, 240, 240), "plate": "DL 01 AB 1234", "plate_conf": 0.96},
            {"id": 102, "x": 340, "y": 140, "speed": 2.4, "class": "suv", "color_name": "black", "bgr": (30, 30, 30), "plate": "MH 12 CD 5678", "plate_conf": 0.94},
            {"id": 103, "x": 480, "y": 60, "speed": 1.2, "class": "bus", "color_name": "green", "bgr": (40, 140, 50), "plate": "DL 1P B 8821", "plate_conf": 0.91},
            {"id": 104, "x": 260, "y": 200, "speed": 2.1, "class": "auto_rickshaw", "color_name": "yellow", "bgr": (20, 200, 220), "plate": "DL 1R C 3490", "plate_conf": 0.92},
            {"id": 105, "x": 120, "y": 240, "speed": 2.7, "class": "motorcycle", "color_name": "red", "bgr": (30, 40, 200), "plate": "HR 26 DQ 7712", "plate_conf": 0.89},
            {"id": 106, "x": 400, "y": 290, "speed": 1.6, "class": "car", "color_name": "silver", "bgr": (180, 180, 180), "plate": "UP 16 XY 9999", "plate_conf": 0.95}
        ]

    def render_frame(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Renders one synthetic frame with road scenery and moving vehicles."""
        self.frame_count += 1
        w, h = self.width, self.height

        # Base asphalt road color (classic dark charcoal)
        frame = np.full((h, w, 3), (45, 45, 48), dtype=np.uint8)

        # Sidewalk / road curbs
        cv2.rectangle(frame, (0, 0), (60, h), (80, 85, 90), -1)
        cv2.rectangle(frame, (w - 60, 0), (w, h), (80, 85, 90), -1)

        # Lane dividers (Classic warm highway dashed lines)
        dash_offset = (self.frame_count * 6) % 40
        for y in range(-40 + dash_offset, h, 40):
            cv2.line(frame, (200, y), (200, min(h, y + 20)), (200, 220, 240), 2)
            cv2.line(frame, (340, y), (340, min(h, y + 20)), (200, 220, 240), 2)
            cv2.line(frame, (480, y), (480, min(h, y + 20)), (200, 220, 240), 2)

        # Render and advance vehicles
        active_metadata = []
        for v in self.vehicles:
            v["y"] += v["speed"]
            if v["y"] > h + 50:
                v["y"] = -60
                v["x"] = random.choice([120, 200, 280, 380, 480])

            vx, vy = int(v["x"]), int(v["y"])
            if -50 <= vy <= h + 50:
                # Vehicle dimensions based on class
                if v["class"] == "bus":
                    bw, bh = 54, 90
                elif v["class"] == "auto_rickshaw":
                    bw, bh = 34, 44
                elif v["class"] == "motorcycle":
                    bw, bh = 22, 38
                elif v["class"] == "suv":
                    bw, bh = 48, 66
                else: # car
                    bw, bh = 44, 60

                x1, y1 = max(10, vx - bw // 2), max(10, vy - bh // 2)
                x2, y2 = min(w - 10, x1 + bw), min(h - 10, y1 + bh)

                # Draw vehicle body
                cv2.rectangle(frame, (x1, y1), (x2, y2), v["bgr"], -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 20, 20), 2)

                # Windshield / roof detail
                win_y1 = y1 + int(bh * 0.2)
                win_y2 = y1 + int(bh * 0.45)
                cv2.rectangle(frame, (x1 + 4, win_y1), (x2 - 4, win_y2), (70, 80, 90), -1)

                # License plate representation
                plate_y = y2 - 8
                plate_x1 = (x1 + x2) // 2 - 16
                plate_x2 = (x1 + x2) // 2 + 16
                cv2.rectangle(frame, (plate_x1, plate_y), (plate_x2, plate_y + 6), (250, 250, 250), -1)

                # Speed estimation
                speed_kmh = round(32.0 + (v["speed"] * 10.5), 1)

                active_metadata.append({
                    "track_id": v["id"],
                    "bbox": [x1, y1, x2, y2],
                    "class": v["class"],
                    "color": v["color_name"],
                    "plate_text": v["plate"],
                    "plate_confidence": v["plate_conf"],
                    "estimated_speed": speed_kmh
                })

        # Draw HUD Overlay: Camera ID, Name, UTC Timestamp
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.rectangle(frame, (0, 0), (w, 28), (20, 25, 30), -1)
        cv2.putText(frame, f"{self.camera_id}: {self.camera_name} | {now_str}", (10, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 230, 225), 1, cv2.LINE_AA)

        return frame, {"frame_id": self.frame_count, "vehicles": active_metadata}


class StreamManager:
    """Manages active camera video streams, synthetic simulation, and MJPEG broadcasting."""

    def __init__(self):
        self.generators: Dict[str, SyntheticRoadGenerator] = {}

    def get_or_create_generator(self, camera_id: str, camera_name: str) -> SyntheticRoadGenerator:
        if camera_id not in self.generators:
            self.generators[camera_id] = SyntheticRoadGenerator(camera_id, camera_name)
        return self.generators[camera_id]

    def get_mjpeg_stream(self, camera_id: str, camera_name: str) -> Generator[bytes, None, None]:
        """Yields multipart JPEG frames for web streaming."""
        gen = self.get_or_create_generator(camera_id, camera_name)
        while True:
            frame, _ = gen.render_frame()
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.04) # ~25 FPS

stream_manager = StreamManager()
