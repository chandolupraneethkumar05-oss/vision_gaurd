# VisionGuard Data Catalog & Benchmark Strategy

In accordance with the SIH26127 technical specification, this catalog documents all benchmark datasets, licenses, annotations, and intended use.

## CityFlow V2 (AI City Challenge)
- **Dataset ID**: `cityflow_v2`
- **Source**: University of Washington & NVIDIA AI City Challenge
- **Official URL**: [https://www.aicitychallenge.org/](https://www.aicitychallenge.org/)
- **License**: Custom Academic Non-Commercial Research License
- **Geography**: Urban Intersections, Multiple Intersections
- **Annotation Format**: `MOT-style tracking + calibrated camera coordinates`
- **Intended Use**: Multi-Target Multi-Camera (MTMC) tracking and cross-camera vehicle association benchmarking
- **Splits**: {"train_cameras": 36, "test_cameras": 10, "total_tracks": 3139}

## VeRi-776 Vehicle Re-Identification
- **Dataset ID**: `veri_776`
- **Source**: State Key Laboratory of Virtual Reality Technology and Systems, Beihang University
- **Official URL**: [https://vehiclereid.github.io/VeRi/](https://vehiclereid.github.io/VeRi/)
- **License**: Research and Educational Use Only
- **Geography**: Urban Surveillance Camera Network (20 cameras)
- **Annotation Format**: `Bounding box crops + vehicle identity labels + visual attributes`
- **Intended Use**: Training and evaluating deep vehicle appearance embedding models
- **Splits**: {"train_images": 37778, "query_images": 1678, "gallery_images": 11579, "num_vehicles": 776}

## Indian License Plate HSRP Benchmark
- **Dataset ID**: `indian_license_plates`
- **Source**: Open-Source Consortium / Kaggle Indian Vehicle Dataset
- **Official URL**: [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)
- **License**: CC BY-SA 4.0 / Open Access
- **Geography**: New Delhi, Mumbai, Bengaluru, Hyderabad, Chennai
- **Annotation Format**: `VOC XML / YOLO-format plate bounding boxes + ground-truth text`
- **Intended Use**: ANPR detection, OCR evaluation, Indian HSRP and Bharat (BH) plate validation
- **Splits**: {"train_plates": 8500, "val_plates": 1500, "test_plates": 2000}

