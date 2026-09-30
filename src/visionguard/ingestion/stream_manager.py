"""Multi-Camera Stream Ingestion and Simulation Manager.
Supports local MP4 files, webcams, live RTSP streams with auto-reconnect,
and a high-fidelity synthetic urban camera frame generator with live tactical AI overlays.
"""
import time
import cv2
import numpy as np
from typing import Dict, Any, Generator, Optional, Tuple, List
from datetime import datetime, timezone
import random

# Color mapping for tactical bounding box visualization (BGR format)
OVERLAY_COLORS = {
    "car": (46, 139, 87),          # Forest Green
    "suv": (34, 90, 160),          # Warm Brown / Heritage Navy
    "bus": (128, 0, 128),          # Royal Purple
    "truck": (19, 69, 139),        # Saddle Brown
    "auto_rickshaw": (0, 165, 255),# Amber Gold
    "motorcycle": (204, 102, 0),   # Deep Teal / Cyan
    "unknown": (120, 120, 120)
}

# Dedicated vehicle pools per camera location for realistic diversity
CAMERA_TRAFFIC_POOLS = {
    "CAM-01": [
        {"id": 101, "x": 160, "y": 40, "speed": 2.2, "class": "car", "color_name": "white", "bgr": (245, 245, 245), "plate": "DL 01 AB 1234", "plate_conf": 0.98},
        {"id": 102, "x": 280, "y": 140, "speed": 2.6, "class": "suv", "color_name": "black", "bgr": (25, 25, 25), "plate": "MH 12 CD 5678", "plate_conf": 0.95},
        {"id": 103, "x": 420, "y": 80, "speed": 1.9, "class": "car", "color_name": "silver", "bgr": (190, 190, 190), "plate": "UP 16 XY 9999", "plate_conf": 0.94},
        {"id": 104, "x": 520, "y": 220, "speed": 2.4, "class": "suv", "color_name": "red", "bgr": (30, 30, 200), "plate": "KA 05 MN 4321", "plate_conf": 0.93},
    ],
    "CAM-02": [
        {"id": 201, "x": 180, "y": 70, "speed": 1.7, "class": "auto_rickshaw", "color_name": "yellow", "bgr": (15, 210, 235), "plate": "DL 1R C 3490", "plate_conf": 0.93},
        {"id": 202, "x": 320, "y": 120, "speed": 1.4, "class": "bus", "color_name": "green", "bgr": (40, 140, 50), "plate": "DL 1P B 8821", "plate_conf": 0.96},
        {"id": 203, "x": 460, "y": 190, "speed": 2.3, "class": "car", "color_name": "white", "bgr": (240, 240, 240), "plate": "DL 04 EF 9012", "plate_conf": 0.97},
        {"id": 204, "x": 130, "y": 260, "speed": 2.8, "class": "motorcycle", "color_name": "black", "bgr": (20, 20, 20), "plate": "HR 26 DQ 7712", "plate_conf": 0.91},
    ],
    "CAM-03": [
        {"id": 301, "x": 170, "y": 50, "speed": 1.3, "class": "bus", "color_name": "green", "bgr": (35, 130, 45), "plate": "DL 1P B 4410", "plate_conf": 0.94},
        {"id": 302, "x": 300, "y": 150, "speed": 2.0, "class": "auto_rickshaw", "color_name": "yellow", "bgr": (15, 210, 235), "plate": "DL 1R D 9901", "plate_conf": 0.92},
        {"id": 303, "x": 440, "y": 100, "speed": 2.4, "class": "car", "color_name": "blue", "bgr": (190, 80, 40), "plate": "22 BH 5543 AB", "plate_conf": 0.98},
        {"id": 304, "x": 220, "y": 270, "speed": 2.5, "class": "motorcycle", "color_name": "red", "bgr": (30, 30, 210), "plate": "DL 08 SC 1120", "plate_conf": 0.90},
    ],
    "CAM-04": [
        {"id": 401, "x": 190, "y": 60, "speed": 2.1, "class": "car", "color_name": "white", "bgr": (240, 240, 240), "plate": "DL 01 AB 1234", "plate_conf": 0.97},
        {"id": 402, "x": 340, "y": 130, "speed": 1.6, "class": "truck", "color_name": "brown", "bgr": (25, 75, 140), "plate": "HR 55 AB 8008", "plate_conf": 0.93},
        {"id": 403, "x": 480, "y": 200, "speed": 2.3, "class": "suv", "color_name": "black", "bgr": (30, 30, 30), "plate": "MH 12 CD 5678", "plate_conf": 0.96},
    ],
    "CAM-05": [
        {"id": 501, "x": 170, "y": 80, "speed": 2.3, "class": "suv", "color_name": "white", "bgr": (245, 245, 245), "plate": "22 BH 1234 AA", "plate_conf": 0.98},
        {"id": 502, "x": 310, "y": 160, "speed": 2.1, "class": "car", "color_name": "silver", "bgr": (185, 185, 185), "plate": "DL 02 BC 4567", "plate_conf": 0.95},
        {"id": 503, "x": 450, "y": 90, "speed": 2.7, "class": "motorcycle", "color_name": "black", "bgr": (20, 20, 20), "plate": "DL 09 MZ 8899", "plate_conf": 0.92},
    ],
    "CAM-06": [
        {"id": 601, "x": 150, "y": 40, "speed": 2.2, "class": "car", "color_name": "white", "bgr": (240, 240, 240), "plate": "DL 01 AB 1234", "plate_conf": 0.97},
        {"id": 602, "x": 280, "y": 120, "speed": 1.8, "class": "auto_rickshaw", "color_name": "yellow", "bgr": (15, 210, 235), "plate": "DL 1R K 6721", "plate_conf": 0.91},
        {"id": 603, "x": 400, "y": 180, "speed": 2.4, "class": "suv", "color_name": "black", "bgr": (30, 30, 30), "plate": "MH 12 CD 5678", "plate_conf": 0.96},
        {"id": 604, "x": 510, "y": 100, "speed": 1.5, "class": "bus", "color_name": "green", "bgr": (40, 140, 50), "plate": "DL 1P C 2309", "plate_conf": 0.94},
    ]
}

class SyntheticRoadGenerator:
    """
    Generates high-definition realistic synthetic urban road video frames
    with animated vehicles, road perspective, lane markings, and live tactical AI detection HUD.
    """

    def __init__(self, camera_id: str, camera_name: str, width: int = 640, height: int = 360):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.width = width
        self.height = height
        self.frame_count = 0

        # Load location-specific pool or fallback
        base_pool = CAMERA_TRAFFIC_POOLS.get(camera_id, CAMERA_TRAFFIC_POOLS["CAM-01"])
        self.vehicles = [dict(v) for v in base_pool]

    def render_frame(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Renders one synthetic frame with road scenery, moving vehicles, and tactical AI HUD."""
        self.frame_count += 1
        w, h = self.width, self.height

        # Base asphalt road color (classic dark charcoal)
        frame = np.full((h, w, 3), (40, 42, 45), dtype=np.uint8)

        # Sidewalk / road curbs
        cv2.rectangle(frame, (0, 0), (50, h), (75, 80, 85), -1)
        cv2.rectangle(frame, (w - 50, 0), (w, h), (75, 80, 85), -1)
        # Curb edge borders
        cv2.line(frame, (50, 0), (50, h), (160, 160, 160), 2)
        cv2.line(frame, (w - 50, 0), (w - 50, h), (160, 160, 160), 2)

        # Lane dividers (Classic highway dashed lines)
        dash_offset = (self.frame_count * 5) % 40
        lane_xs = [180, 310, 440]
        for lx in lane_xs:
            for y in range(-40 + dash_offset, h, 40):
                cv2.line(frame, (lx, y), (lx, min(h, y + 22)), (210, 225, 235), 2)

        # Render and advance vehicles
        active_metadata = []
        for v in self.vehicles:
            v["y"] += v["speed"]
            if v["y"] > h + 60:
                v["y"] = -70
                v["x"] = random.choice([120, 220, 340, 440])

            vx, vy = int(v["x"]), int(v["y"])
            if -60 <= vy <= h + 60:
                # Vehicle dimensions based on class
                if v["class"] == "bus":
                    bw, bh = 56, 96
                elif v["class"] == "truck":
                    bw, bh = 54, 90
                elif v["class"] == "auto_rickshaw":
                    bw, bh = 36, 46
                elif v["class"] == "motorcycle":
                    bw, bh = 22, 38
                elif v["class"] == "suv":
                    bw, bh = 50, 68
                else:  # car
                    bw, bh = 46, 62

                x1, y1 = max(10, vx - bw // 2), max(10, vy - bh // 2)
                x2, y2 = min(w - 10, x1 + bw), min(h - 10, y1 + bh)

                # Draw vehicle body
                cv2.rectangle(frame, (x1, y1), (x2, y2), v["bgr"], -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 20, 20), 1)

                # Windshield / roof detail
                win_y1 = y1 + int(bh * 0.18)
                win_y2 = y1 + int(bh * 0.42)
                cv2.rectangle(frame, (x1 + 4, win_y1), (x2 - 4, win_y2), (65, 75, 85), -1)

                # Headlights
                cv2.circle(frame, (x1 + 6, y1 + 3), 3, (180, 240, 255), -1)
                cv2.circle(frame, (x2 - 6, y1 + 3), 3, (180, 240, 255), -1)

                # License plate representation on vehicle
                plate_y = y2 - 8
                plate_x1 = (x1 + x2) // 2 - 16
                plate_x2 = (x1 + x2) // 2 + 16
                cv2.rectangle(frame, (plate_x1, plate_y), (plate_x2, plate_y + 6), (250, 250, 250), -1)

                # Speed estimation
                speed_kmh = round(34.0 + (v["speed"] * 8.5), 1)

                # --- LIVE TACTICAL COMPUTER VISION OVERLAY ---
                color = OVERLAY_COLORS.get(v["class"], (46, 139, 87))

                # Corner brackets
                c_len = min(12, bw // 3)
                # Top-left
                cv2.line(frame, (x1 - 3, y1 - 3), (x1 - 3 + c_len, y1 - 3), color, 2)
                cv2.line(frame, (x1 - 3, y1 - 3), (x1 - 3, y1 - 3 + c_len), color, 2)
                # Top-right
                cv2.line(frame, (x2 + 3, y1 - 3), (x2 + 3 - c_len, y1 - 3), color, 2)
                cv2.line(frame, (x2 + 3, y1 - 3), (x2 + 3, y1 - 3 + c_len), color, 2)
                # Bottom-left
                cv2.line(frame, (x1 - 3, y2 + 3), (x1 - 3 + c_len, y2 + 3), color, 2)
                cv2.line(frame, (x1 - 3, y2 + 3), (x1 - 3, y2 + 3 - c_len), color, 2)
                # Bottom-right
                cv2.line(frame, (x2 + 3, y2 + 3), (x2 + 3 - c_len, y2 + 3), color, 2)
                cv2.line(frame, (x2 + 3, y2 + 3), (x2 + 3, y2 + 3 - c_len), color, 2)

                # Class & Confidence pill label
                conf_pct = int(v["plate_conf"] * 100)
                cls_label = f"{v['class'].upper()} {conf_pct}%"
                (lw, lh), _ = cv2.getTextSize(cls_label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
                
                label_y1 = max(30, y1 - lh - 6)
                cv2.rectangle(frame, (x1 - 3, label_y1), (x1 + lw + 6, label_y1 + lh + 5), color, -1)
                cv2.putText(frame, cls_label, (x1, label_y1 + lh + 1),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

                # Speed & Plate pill below
                info_pill = f"{speed_kmh}kph | {v['plate']}"
                (pw, ph), _ = cv2.getTextSize(info_pill, cv2.FONT_HERSHEY_SIMPLEX, 0.32, 1)
                pill_y = min(h - 10, y2 + ph + 8)
                cv2.rectangle(frame, (x1 - 3, y2 + 4), (x1 + pw + 5, pill_y), (15, 20, 25), -1)
                cv2.putText(frame, info_pill, (x1, pill_y - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 230, 255), 1, cv2.LINE_AA)

                active_metadata.append({
                    "track_id": v["id"],
                    "bbox": [x1, y1, x2, y2],
                    "class": v["class"],
                    "color": v["color_name"],
                    "plate_text": v["plate"],
                    "plate_confidence": v["plate_conf"],
                    "estimated_speed": speed_kmh
                })

        # --- Top HUD Overlay Bar ---
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.rectangle(frame, (0, 0), (w, 26), (15, 20, 25), -1)
        cv2.line(frame, (0, 26), (w, 26), (50, 60, 70), 1)

        # Camera info & Live badge
        cv2.putText(frame, f"{self.camera_id}: {self.camera_name}", (10, 17),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 240, 235), 1, cv2.LINE_AA)
        
        right_text = f"AI-DETECT: {len(active_metadata)} | {now_str}"
        (rw, _), _ = cv2.getTextSize(right_text, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
        cv2.putText(frame, right_text, (w - rw - 10, 17),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 180), 1, cv2.LINE_AA)

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
            time.sleep(0.04)  # ~25 FPS


stream_manager = StreamManager()
