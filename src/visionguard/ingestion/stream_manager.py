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
    with authentic vehicle silhouettes, drop-shadows, headlights, wheels,
    asphalt texture, curbs, and live tactical AI detection HUD.
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

    def _draw_road_environment(self, frame: np.ndarray, w: int, h: int):
        """Renders realistic textured asphalt, Indian municipal painted curbs, and lane markings."""
        # Asphalt base color
        frame[:, :] = (38, 40, 42)

        # Sidewalk pavements
        cv2.rectangle(frame, (0, 0), (52, h), (72, 75, 78), -1)
        cv2.rectangle(frame, (w - 52, 0), (w, h), (72, 75, 78), -1)

        # Alternating black & yellow safety curbs (Indian Smart City standard)
        curb_h = 24
        for y in range(0, h, curb_h):
            is_yellow = (y // curb_h) % 2 == 0
            curb_color = (0, 200, 240) if is_yellow else (25, 25, 25)
            # Left curb
            cv2.rectangle(frame, (48, y), (54, min(h, y + curb_h)), curb_color, -1)
            # Right curb
            cv2.rectangle(frame, (w - 54, y), (w - 48, min(h, y + curb_h)), curb_color, -1)

        # Solid white boundary edge lines
        cv2.line(frame, (56, 0), (56, h), (220, 225, 230), 2)
        cv2.line(frame, (w - 56, 0), (w - 56, h), (220, 225, 230), 2)

        # Dashed lane dividers with realistic perspective motion
        dash_offset = (self.frame_count * 5) % 40
        lane_xs = [190, 320, 450]
        for lx in lane_xs:
            for y in range(-40 + dash_offset, h, 40):
                cv2.line(frame, (lx, y), (lx, min(h, y + 22)), (230, 235, 240), 2)

        # Subtle road tire wear tracks along the 3 active driving lanes
        tire_lanes = [140, 255, 385, 510]
        for tx in tire_lanes:
            overlay = frame.copy()
            cv2.line(overlay, (tx, 0), (tx, h), (28, 30, 32), 16)
            cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    def _draw_realistic_vehicle(self, frame: np.ndarray, v: Dict[str, Any], vx: int, vy: int, w: int, h: int) -> Tuple[int, int, int, int]:
        """Draws realistic vehicle silhouette with drop shadow, wheels, headlights, and class-specific details."""
        v_class = v["class"]
        bgr = v["bgr"]

        # Dimensions based on vehicle category
        if v_class == "bus":
            bw, bh = 60, 112
        elif v_class == "truck":
            bw, bh = 58, 102
        elif v_class == "auto_rickshaw":
            bw, bh = 38, 48
        elif v_class == "motorcycle":
            bw, bh = 22, 42
        elif v_class == "suv":
            bw, bh = 52, 74
        else:  # car / sedan
            bw, bh = 48, 66

        x1 = max(10, vx - bw // 2)
        y1 = max(10, vy - bh // 2)
        x2 = min(w - 10, x1 + bw)
        y2 = min(h - 10, y1 + bh)

        # 1. Soft Ambient Drop Shadow Underneath Vehicle (Alpha Blended)
        shadow_overlay = frame.copy()
        cv2.ellipse(shadow_overlay, (vx, vy + 4), (int(bw * 0.65), int(bh * 0.60)), 0, 0, 360, (12, 14, 16), -1)
        cv2.addWeighted(shadow_overlay, 0.55, frame, 0.45, 0, frame)

        # 2. Wheels / Tyres on the sides
        if v_class in ["car", "suv", "truck", "bus"]:
            wheel_w, wheel_h = 5, 12
            # Front wheels
            cv2.rectangle(frame, (x1 - 3, y1 + 10), (x1, y1 + 10 + wheel_h), (18, 18, 18), -1)
            cv2.rectangle(frame, (x2, y1 + 10), (x2 + 3, y1 + 10 + wheel_h), (18, 18, 18), -1)
            # Rear wheels
            cv2.rectangle(frame, (x1 - 3, y2 - 18), (x1, y2 - 18 + wheel_h), (18, 18, 18), -1)
            cv2.rectangle(frame, (x2, y2 - 18), (x2 + 3, y2 - 18 + wheel_h), (18, 18, 18), -1)
            # Silver hubcaps
            cv2.line(frame, (x1 - 2, y1 + 16), (x1 - 1, y1 + 16), (160, 160, 160), 1)
            cv2.line(frame, (x2 + 1, y1 + 16), (x2 + 2, y1 + 16), (160, 160, 160), 1)
            cv2.line(frame, (x1 - 2, y2 - 12), (x1 - 1, y2 - 12), (160, 160, 160), 1)
            cv2.line(frame, (x2 + 1, y2 - 12), (x2 + 2, y2 - 12), (160, 160, 160), 1)
        elif v_class == "auto_rickshaw":
            # 3 wheels: 1 front, 2 rear
            cv2.rectangle(frame, (vx - 2, y1 - 2), (vx + 2, y1 + 6), (18, 18, 18), -1)
            cv2.rectangle(frame, (x1 - 2, y2 - 12), (x1 + 1, y2), (18, 18, 18), -1)
            cv2.rectangle(frame, (x2 - 1, y2 - 12), (x2 + 2, y2), (18, 18, 18), -1)

        # 3. Headlight Light Cones projecting onto the road
        if y1 > 20:
            beam_overlay = frame.copy()
            left_pts = np.array([[x1 + 6, y1], [x1 - 8, max(0, y1 - 35)], [x1 + 14, max(0, y1 - 35)]], np.int32)
            right_pts = np.array([[x2 - 6, y1], [x2 - 14, max(0, y1 - 35)], [x2 + 8, max(0, y1 - 35)]], np.int32)
            cv2.fillPoly(beam_overlay, [left_pts], (180, 240, 255))
            cv2.fillPoly(beam_overlay, [right_pts], (180, 240, 255))
            cv2.addWeighted(beam_overlay, 0.20, frame, 0.80, 0, frame)

        # 4. Main Body & Specific Silhouettes
        if v_class == "auto_rickshaw":
            # Distinctive Delhi Bajaj 3-wheeler: Yellow canopy roof, CNG green lower skirts
            cv2.rectangle(frame, (x1 + 2, y1 + 8), (x2 - 2, y2 - 2), (35, 125, 45), -1) # Green lower body
            cv2.rectangle(frame, (x1 + 1, y1 + 10), (x2 - 1, y2 - 10), (10, 210, 245), -1) # Bright yellow canopy
            cv2.circle(frame, (vx, y1 + 8), int(bw * 0.45), (10, 210, 245), -1) # Front rounded cowl
            # Black handlebar console
            cv2.line(frame, (vx - 6, y1 + 12), (vx + 6, y1 + 12), (20, 20, 20), 2)
            # Black rear passenger vinyl seat
            cv2.rectangle(frame, (x1 + 5, y2 - 12), (x2 - 5, y2 - 4), (25, 25, 25), -1)

        elif v_class == "bus":
            # Delhi Transport Corporation (DTC) low-floor electric city bus
            cv2.rectangle(frame, (x1, y1), (x2, y2), (35, 130, 45), -1) # Green body
            # White roof panel
            cv2.rectangle(frame, (x1 + 4, y1 + 18), (x2 - 4, y2 - 12), (235, 240, 235), -1)
            # Panoramic front windshield
            cv2.rectangle(frame, (x1 + 3, y1 + 2), (x2 - 3, y1 + 16), (55, 65, 75), -1)
            # Amber LED Destination Display Board
            cv2.rectangle(frame, (x1 + 8, y1 + 2), (x2 - 8, y1 + 7), (0, 180, 255), -1)
            # Roof AC units
            cv2.rectangle(frame, (vx - 10, y1 + 28), (vx + 10, y1 + 46), (180, 185, 190), -1)
            cv2.rectangle(frame, (vx - 10, y1 + 60), (vx + 10, y1 + 78), (180, 185, 190), -1)

        elif v_class == "truck":
            # Heavy Commercial Rigid Truck
            cv2.rectangle(frame, (x1, y1), (x2, y1 + 30), (30, 45, 65), -1) # Front cab
            cv2.rectangle(frame, (x1 - 1, y1 + 32), (x2 + 1, y2), bgr, -1) # Cargo container/bed
            # Container ribs
            for cy in range(y1 + 40, y2 - 8, 12):
                cv2.line(frame, (x1 + 2, cy), (x2 - 2, cy), (20, 20, 20), 1)
            # Windshield
            cv2.rectangle(frame, (x1 + 4, y1 + 6), (x2 - 4, y1 + 22), (60, 70, 80), -1)

        elif v_class == "motorcycle":
            # Two-wheeler motorcycle with helmeted rider
            cv2.rectangle(frame, (vx - 4, y1 + 4), (vx + 4, y2 - 4), (30, 30, 30), -1) # Chassis
            cv2.circle(frame, (vx, y1 + 10), 5, bgr, -1) # Fuel tank
            cv2.circle(frame, (vx, y1 + 20), 6, (0, 215, 255), -1) # Helmeted rider (yellow safety helmet)
            cv2.line(frame, (vx - 8, y1 + 8), (vx + 8, y1 + 8), (20, 20, 20), 2) # Handlebars

        else: # Car or SUV
            # Aerodynamic body shape with specular highlights
            cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, -1)
            # Body outline
            cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 22, 24), 1)

            # Curved front windshield
            cv2.rectangle(frame, (x1 + 4, y1 + int(bh * 0.18)), (x2 - 4, y1 + int(bh * 0.38)), (50, 60, 72), -1)
            # Glass reflection streak
            cv2.line(frame, (x1 + 8, y1 + int(bh * 0.20)), (x2 - 12, y1 + int(bh * 0.36)), (140, 160, 180), 1)

            # Roof Panel with highlight
            cv2.rectangle(frame, (x1 + 4, y1 + int(bh * 0.38)), (x2 - 4, y1 + int(bh * 0.70)), bgr, -1)
            cv2.line(frame, (vx - 1, y1 + int(bh * 0.38)), (vx - 1, y1 + int(bh * 0.70)), (240, 240, 240), 1)

            # Rear window
            cv2.rectangle(frame, (x1 + 5, y1 + int(bh * 0.70)), (x2 - 5, y1 + int(bh * 0.85)), (40, 48, 56), -1)

            # Side mirrors
            cv2.rectangle(frame, (x1 - 4, y1 + int(bh * 0.26)), (x1, y1 + int(bh * 0.32)), bgr, -1)
            cv2.rectangle(frame, (x2, y1 + int(bh * 0.26)), (x2 + 4, y1 + int(bh * 0.32)), bgr, -1)

            # SUV Roof rack rails
            if v_class == "suv":
                cv2.line(frame, (x1 + 6, y1 + int(bh * 0.36)), (x1 + 6, y1 + int(bh * 0.72)), (30, 30, 30), 2)
                cv2.line(frame, (x2 - 6, y1 + int(bh * 0.36)), (x2 - 6, y1 + int(bh * 0.72)), (30, 30, 30), 2)

        # 5. Front Headlights & Rear Taillights
        cv2.circle(frame, (x1 + 6, y1 + 3), 3, (200, 245, 255), -1) # Left Headlight
        cv2.circle(frame, (x2 - 6, y1 + 3), 3, (200, 245, 255), -1) # Right Headlight
        cv2.rectangle(frame, (x1 + 5, y2 - 4), (x1 + 12, y2), (20, 20, 220), -1) # Left Taillight
        cv2.rectangle(frame, (x2 - 12, y2 - 4), (x2 - 5, y2), (20, 20, 220), -1) # Right Taillight

        # 6. High-Security Registration Plate (HSRP) with blue IND strip
        plate_w = min(36, bw - 14)
        plate_x1 = vx - plate_w // 2
        plate_x2 = plate_x1 + plate_w
        plate_y1 = y2 - 7
        plate_y2 = y2 - 1
        cv2.rectangle(frame, (plate_x1, plate_y1), (plate_x2, plate_y2), (245, 245, 245), -1)
        cv2.rectangle(frame, (plate_x1, plate_y1), (plate_x1 + 4, plate_y2), (180, 60, 20), -1) # Blue IND strip

        return x1, y1, x2, y2

    def render_frame(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Renders one high-definition synthetic frame with realistic visuals and tactical AI HUD."""
        self.frame_count += 1
        w, h = self.width, self.height
        frame = np.empty((h, w, 3), dtype=np.uint8)

        # Render realistic road environment
        self._draw_road_environment(frame, w, h)

        # Render and advance vehicles
        active_metadata = []
        for v in self.vehicles:
            v["y"] += v["speed"]
            if v["y"] > h + 70:
                v["y"] = -80
                v["x"] = random.choice([130, 230, 350, 470])

            vx, vy = int(v["x"]), int(v["y"])
            if -70 <= vy <= h + 70:
                x1, y1, x2, y2 = self._draw_realistic_vehicle(frame, v, vx, vy, w, h)

                # Speed estimation
                speed_kmh = round(34.0 + (v["speed"] * 8.5), 1)

                # --- LIVE TACTICAL COMPUTER VISION OVERLAY ---
                color = OVERLAY_COLORS.get(v["class"], (46, 139, 87))

                # Sleek tactical corner brackets
                c_len = min(12, (x2 - x1) // 3)
                thick = 2
                # Top-left
                cv2.line(frame, (x1 - 3, y1 - 3), (x1 - 3 + c_len, y1 - 3), color, thick)
                cv2.line(frame, (x1 - 3, y1 - 3), (x1 - 3, y1 - 3 + c_len), color, thick)
                # Top-right
                cv2.line(frame, (x2 + 3, y1 - 3), (x2 + 3 - c_len, y1 - 3), color, thick)
                cv2.line(frame, (x2 + 3, y1 - 3), (x2 + 3, y1 - 3 + c_len), color, thick)
                # Bottom-left
                cv2.line(frame, (x1 - 3, y2 + 3), (x1 - 3 + c_len, y2 + 3), color, thick)
                cv2.line(frame, (x1 - 3, y2 + 3), (x1 - 3, y2 + 3 - c_len), color, thick)
                # Bottom-right
                cv2.line(frame, (x2 + 3, y2 + 3), (x2 + 3 - c_len, y2 + 3), color, thick)
                cv2.line(frame, (x2 + 3, y2 + 3), (x2 + 3, y2 + 3 - c_len), color, thick)

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

        # --- Professional CCTV On-Screen Display (OSD) Bar ---
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.rectangle(frame, (0, 0), (w, 26), (12, 15, 18), -1)
        cv2.line(frame, (0, 26), (w, 26), (45, 55, 65), 1)

        # Camera identification and live OSD text
        osd_title = f"{self.camera_id}: {self.camera_name.upper()}"
        cv2.putText(frame, osd_title, (10, 17),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (235, 245, 240), 1, cv2.LINE_AA)

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
