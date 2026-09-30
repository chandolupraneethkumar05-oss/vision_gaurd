"""Generate synthetic multi-camera urban vehicle observations and journeys."""
import random
from datetime import datetime, timedelta, timezone
from visionguard.database.db_manager import db
from visionguard.association.journey_reconstructor import JourneyReconstructor
from visionguard.analytics.anomaly_detector import TrafficAnomalyDetector

def generate_synthetic_data(num_vehicles: int = 25):
    print(f"Generating synthetic traffic dataset for {num_vehicles} vehicles...")
    reconstructor = JourneyReconstructor()
    detector = TrafficAnomalyDetector()
    cameras = db.get_all_cameras()
    cam_ids = [c["camera_id"] for c in cameras]

    indian_states = ["DL", "MH", "KA", "UP", "HR", "TS", "GJ", "TN"]
    v_classes = ["car", "suv", "motorcycle", "auto_rickshaw", "bus", "truck"]
    colors = ["white", "black", "silver", "red", "blue", "yellow"]

    base_time = datetime.now(timezone.utc) - timedelta(hours=3)

    for i in range(num_vehicles):
        state = random.choice(indian_states)
        rto = random.randint(1, 14)
        series = random.choice(["AB", "CD", "XY", "MN", "DQ", "EF", "KA", "PB"])
        num = random.randint(1000, 9999)
        plate_str = f"{state} {rto:02d} {series} {num}"
        v_class = random.choice(v_classes)
        color = random.choice(colors)
        veh_id = f"VEH-{plate_str.replace(' ', '')}"

        # Register vehicle identity
        db.upsert_vehicle_identity({
            "global_vehicle_id": veh_id,
            "primary_plate": plate_str,
            "vehicle_class": v_class,
            "color": color
        })

        # Generate a 2 to 4 camera transit journey along graph
        journey_length = random.randint(2, 4)
        start_idx = random.randint(0, len(cam_ids) - journey_length)
        selected_cams = cam_ids[start_idx:start_idx + journey_length]

        curr_time = base_time + timedelta(minutes=random.randint(0, 150))
        journey_obs = []

        for cam_id in selected_cams:
            cam_info = next(c for c in cameras if c["camera_id"] == cam_id)
            speed = round(random.uniform(32.0, 72.0), 1)

            obs = {
                "camera_id": cam_id,
                "timestamp": curr_time.isoformat(),
                "frame_id": random.randint(100, 5000),
                "track_id": random.randint(1, 99),
                "bbox_x1": random.randint(50, 250),
                "bbox_y1": random.randint(80, 180),
                "bbox_x2": random.randint(300, 520),
                "bbox_y2": random.randint(220, 340),
                "vehicle_class": v_class,
                "confidence": round(random.uniform(0.88, 0.98), 2),
                "estimated_speed": speed,
                "color": color,
                "plate_text": plate_str,
                "plate_confidence": round(random.uniform(0.90, 0.99), 2),
                "embedding_json": None
            }
            db.insert_observation(obs)
            journey_obs.append(obs)
            
            # Check for anomalies / speeding
            detector.evaluate_observation(obs, cam_info)

            # Advance transit time (60-180 seconds between junctions)
            curr_time += timedelta(seconds=random.randint(60, 180))

        # Reconstruct journey
        reconstructor.reconstruct_from_observations(veh_id, journey_obs)

    print(f"Successfully populated database with synthetic urban vehicles, observations, and journeys.")

if __name__ == "__main__":
    generate_synthetic_data()
