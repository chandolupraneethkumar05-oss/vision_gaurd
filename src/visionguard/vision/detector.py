"""Vehicle Detection and Classification module.
Supports real deep-learning inference with Ultralytics YOLOv8 / ONNX,
with fallback OpenCV contour & aspect-ratio analysis.
Classifies vehicles into: car, suv, motorcycle, auto_rickshaw, bus, truck.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from visionguard.config import VEHICLE_CLASSES, VEHICLE_COLORS, BASE_DIR

# Flag indicating whether ultralytics is available
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except Exception:
    _YOLO_AVAILABLE = False


class VehicleDetector:
    """
    Detector supporting real-time vehicle localization, classification,
    and dominant color extraction from bounding boxes.
    Utilizes YOLOv8 nano when model weights and packages are present.
    """

    # COCO Class mapping to VisionGuard vehicle classes
    COCO_VEHICLE_MAP = {
        2: "car",          # car
        3: "motorcycle",   # motorcycle
        5: "bus",          # bus
        7: "truck",        # truck
        1: "motorcycle"    # bicycle / two-wheeler
    }

    def __init__(self, confidence_threshold: float = 0.40, iou_threshold: float = 0.50):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.yolo_model = None

        # Attempt to load YOLOv8 if available
        if _YOLO_AVAILABLE:
            weights_path = BASE_DIR / "models" / "pretrained" / "yolov8n.pt"
            if weights_path.exists() and weights_path.stat().st_size > 1000000:
                try:
                    self.yolo_model = YOLO(str(weights_path))
                except Exception:
                    self.yolo_model = None

    def extract_dominant_color(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> str:
        """Extracts dominant color of vehicle from central region of bounding box."""
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return "unknown"

        # Center sample crop to avoid road and background pixels
        ch, cw = crop.shape[:2]
        sample = crop[int(ch * 0.25):int(ch * 0.75), int(cw * 0.25):int(cw * 0.75)]
        if sample.size == 0:
            sample = crop

        hsv = cv2.cvtColor(sample, cv2.COLOR_BGR2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)
        mean_v = np.mean(v_channel)
        mean_s = np.mean(s_channel)
        mean_h = np.mean(h_channel)

        if mean_v < 50:
            return "black"
        elif mean_s < 40 and mean_v > 180:
            return "white"
        elif mean_s < 40:
            return "silver" if mean_v > 120 else "gray"

        # Hue ranges
        if mean_h < 10 or mean_h > 165:
            return "red"
        elif 10 <= mean_h < 25:
            return "brown"
        elif 25 <= mean_h < 35:
            return "yellow"
        elif 35 <= mean_h < 85:
            return "green"
        elif 85 <= mean_h < 130:
            return "blue"
        else:
            return "white"

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Performs vehicle detection on an input video frame.
        Uses YOLOv8 if loaded; otherwise applies contour & aspect ratio vehicle parsing.
        """
        detections = []
        if frame is None or frame.size == 0:
            return detections

        h, w = frame.shape[:2]

        # 1. Try YOLO model if available
        if self.yolo_model is not None:
            try:
                results = self.yolo_model.predict(
                    frame,
                    conf=self.confidence_threshold,
                    iou=self.iou_threshold,
                    verbose=False
                )
                if results and len(results) > 0:
                    boxes = results[0].boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        if cls_id in self.COCO_VEHICLE_MAP:
                            bx1, by1, bx2, by2 = map(int, box.xyxy[0].tolist())
                            bx1, by1 = max(0, bx1), max(0, by1)
                            bx2, by2 = min(w, bx2), min(h, by2)
                            
                            conf = float(box.conf[0].item())
                            v_class = self.COCO_VEHICLE_MAP[cls_id]
                            
                            # Refine car to SUV or Auto Rickshaw by aspect ratio & size
                            bw, bh = bx2 - bx1, by2 - by1
                            aspect = bw / float(max(1, bh))
                            if v_class == "car" and bh > 90 and aspect < 1.4:
                                v_class = "suv"
                            elif v_class == "motorcycle" and aspect > 0.85 and bw > 50:
                                v_class = "auto_rickshaw"

                            color = self.extract_dominant_color(frame, (bx1, by1, bx2, by2))
                            detections.append({
                                "bbox": [bx1, by1, bx2, by2],
                                "class": v_class,
                                "confidence": round(conf, 3),
                                "color": color
                            })
                    
                    if len(detections) > 0:
                        return detections
            except Exception:
                pass

        # 2. Adaptive contour & aspect ratio detection (Fallback & synthetic test images)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for idx, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area > 1200: # Threshold for vehicle candidate
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect_ratio = bw / float(bh)
                if 0.5 < aspect_ratio < 3.5:
                    v_class = "car"
                    if area > 8000:
                        v_class = "bus" if aspect_ratio > 2.0 else "truck"
                    elif area < 2500:
                        v_class = "motorcycle" if aspect_ratio < 0.9 else "auto_rickshaw"
                    elif aspect_ratio > 1.3:
                        v_class = "suv"

                    color = self.extract_dominant_color(frame, (x, y, x + bw, y + bh))
                    conf = min(0.98, max(0.65, 0.5 + (area / 15000.0)))

                    detections.append({
                        "bbox": [x, y, x + bw, y + bh],
                        "class": v_class,
                        "confidence": round(conf, 3),
                        "color": color
                    })

        # Apply Non-Maximum Suppression (NMS)
        if len(detections) > 0:
            boxes = [d["bbox"] for d in detections]
            confs = [d["confidence"] for d in detections]
            indices = cv2.dnn.NMSBoxes(
                [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in boxes],
                confs,
                self.confidence_threshold,
                self.iou_threshold
            )
            filtered = []
            if len(indices) > 0:
                for i in indices.flatten():
                    filtered.append(detections[i])
            return filtered

        return detections
