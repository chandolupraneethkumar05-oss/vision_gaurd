"""Dataset management and catalog utility for VisionGuard.
Supports CityFlow (MTMC), VeRi-776 (Vehicle Re-ID), and Indian License Plate Benchmarks.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List

DATA_CATALOG = {
    "datasets": [
        {
            "id": "cityflow_v2",
            "name": "CityFlow V2 (AI City Challenge)",
            "source": "University of Washington & NVIDIA AI City Challenge",
            "url": "https://www.aicitychallenge.org/",
            "license": "Custom Academic Non-Commercial Research License",
            "geography": "Urban Intersections, Multiple Intersections",
            "annotation_format": "MOT-style tracking + calibrated camera coordinates",
            "intended_use": "Multi-Target Multi-Camera (MTMC) tracking and cross-camera vehicle association benchmarking",
            "splits": {"train_cameras": 36, "test_cameras": 10, "total_tracks": 3139},
            "local_path": "data/raw/cityflow_v2"
        },
        {
            "id": "veri_776",
            "name": "VeRi-776 Vehicle Re-Identification",
            "source": "State Key Laboratory of Virtual Reality Technology and Systems, Beihang University",
            "url": "https://vehiclereid.github.io/VeRi/",
            "license": "Research and Educational Use Only",
            "geography": "Urban Surveillance Camera Network (20 cameras)",
            "annotation_format": "Bounding box crops + vehicle identity labels + visual attributes",
            "intended_use": "Training and evaluating deep vehicle appearance embedding models",
            "splits": {"train_images": 37778, "query_images": 1678, "gallery_images": 11579, "num_vehicles": 776},
            "local_path": "data/raw/veri_776"
        },
        {
            "id": "indian_license_plates",
            "name": "Indian License Plate HSRP Benchmark",
            "source": "Open-Source Consortium / Kaggle Indian Vehicle Dataset",
            "url": "https://www.kaggle.com/datasets",
            "license": "CC BY-SA 4.0 / Open Access",
            "geography": "New Delhi, Mumbai, Bengaluru, Hyderabad, Chennai",
            "annotation_format": "VOC XML / YOLO-format plate bounding boxes + ground-truth text",
            "intended_use": "ANPR detection, OCR evaluation, Indian HSRP and Bharat (BH) plate validation",
            "splits": {"train_plates": 8500, "val_plates": 1500, "test_plates": 2000},
            "local_path": "data/raw/indian_license_plates"
        }
    ]
}

def export_data_catalog():
    """Writes data catalog metadata JSON and markdown documentation."""
    docs_path = Path("docs/datasets")
    docs_path.mkdir(parents=True, exist_ok=True)
    catalog_file = docs_path / "data_catalog.json"
    
    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(DATA_CATALOG, f, indent=2)

    md_file = docs_path / "README.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# VisionGuard Data Catalog & Benchmark Strategy\n\n")
        f.write("In accordance with the SIH26127 technical specification, this catalog documents all benchmark datasets, licenses, annotations, and intended use.\n\n")
        for ds in DATA_CATALOG["datasets"]:
            f.write(f"## {ds['name']}\n")
            f.write(f"- **Dataset ID**: `{ds['id']}`\n")
            f.write(f"- **Source**: {ds['source']}\n")
            f.write(f"- **Official URL**: [{ds['url']}]({ds['url']})\n")
            f.write(f"- **License**: {ds['license']}\n")
            f.write(f"- **Geography**: {ds['geography']}\n")
            f.write(f"- **Annotation Format**: `{ds['annotation_format']}`\n")
            f.write(f"- **Intended Use**: {ds['intended_use']}\n")
            f.write(f"- **Splits**: {json.dumps(ds['splits'])}\n\n")

    print(f"Exported data catalog to {catalog_file} and {md_file}")

if __name__ == "__main__":
    export_data_catalog()
