"""Database seeding script for VisionGuard."""
import os
from visionguard.config import DB_PATH
from visionguard.database.db_manager import db
from scripts.generate_synthetic_data import generate_synthetic_data

def reset_and_seed():
    print("Initializing VisionGuard database...")
    db.init_db()
    generate_synthetic_data(num_vehicles=20)
    print("Database seeding completed.")

if __name__ == "__main__":
    reset_and_seed()
