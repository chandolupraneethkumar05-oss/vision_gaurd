# VisionGuard System Architecture & Technical Specification

**Project**: AI-Powered Multi-Camera Urban Traffic Intelligence Platform (SIH26127)  
**Version**: 1.0.0  

---

## 1. Executive Summary

VisionGuard is a production-grade urban traffic monitoring, surveillance, and visual intelligence platform. It fuses real-time computer vision, High-Security Registration Plate (HSRP) recognition, appearance-based vehicle re-identification (Re-ID), and topological spatio-temporal road graphs to track vehicles across non-overlapping municipal cameras while computing highway-grade traffic analytics.

---

## 2. Competitive Landscape & Technical Differentiation

Based on industry analysis of the top 5 commercial traffic and video analytics platforms, VisionGuard directly resolves key architectural and operational bottlenecks:

| Platform | Core Strength | Critical Drawbacks & Limitations | VisionGuard Solution |
| :--- | :--- | :--- | :--- |
| **BriefCam** | Video synopsis, forensic search | Extremely high GPU server footprint; siloed from real-time road topology; high false alert rates in dense crowds. | Lightweight, edge/CPU-optimized pipeline; topological spatio-temporal graph eliminates cross-camera false alarms. |
| **Miovision** | Signal performance, traffic surveying | Proprietary hardware lock-in (Scout pods); rigid camera placement requirements; poor cross-camera Re-ID. | Universal camera ingestion (RTSP/IP/MP4/Webcam/Simulated) without proprietary hardware appliances. |
| **GoodVision** | SaaS traffic surveying & modeling | Primarily post-processing batch tool; high latency for real-time security alerts; lacks Indian ANPR parser. | Real-time WebSocket streaming; sub-20ms inference pipeline; instant automated security watchlist triggers. |
| **Rekor Systems** | ALPR & vehicle identification | Historical struggle with non-standard international plates (Indian double-line/regional fonts); lack of route physics. | Specialized Indian MoRTH ANPR validator (HSRP, Bharat Series, Commercial, EV) with temporal frame voting buffer. |
| **Videonetics** | Indian smart city enforcement | Cluttered legacy desktop UI with high-contrast dark-neon themes causing intense 8-hour operator eye fatigue. | **Classic Ergonomic Visual System**: Warm parchment beige, hunter green, saddle leather, and slate navy for restful 24/7 operations. |

---

## 3. End-to-End Pipeline by Stages

### Stage 1: Video & Camera Ingestion
- Ingests multiple simultaneous RTSP streams, MP4 video files, webcams, and synthetic road generators.
- Built-in automatic reconnect logic, timestamp synchronization, and frame buffering.

### Stage 2 & 3: Vehicle Detection & Single-Camera Tracking
- Multi-class localization: `car`, `suv`, `motorcycle`, `auto_rickshaw`, `bus`, `truck`.
- Non-Maximum Suppression (NMS) and color feature sampling.
- ByteTrack-inspired tracking with trajectory smoothing, pixel-to-meter speed estimation, and ID-switch prevention.

### Stage 4: Indian ANPR & HSRP Parsing
- MoRTH-compliant format validation using strict regular expressions:
  - Standard HSRP: `^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$` (e.g., `DL 01 AB 1234`)
  - Bharat Series: `^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$` (e.g., `22 BH 5543 AB`)
  - Validates against all 36 Indian State and Union Territory RTO codes.
- **Temporal Voting Buffer (`PlateVotingBuffer`)**: Aggregates multi-frame OCR predictions for each track ID to filter sensor noise and motion blur.

### Stage 5: Vehicle Re-Identification (Re-ID)
- Illumination-invariant appearance descriptor combining HSV color distributions and spatial grid moments.
- Cosine similarity matching and ranked candidate retrieval across camera gallery.

### Stage 6: Multi-Modal Bayesian Association
- Fuses three orthogonal evidence sources into a single probabilistic match score:
  $$S = w_{\text{plate}} \cdot S_{\text{plate}} + w_{\text{appearance}} \cdot S_{\text{cosine}} + w_{\text{spatial}} \cdot \text{Pr}(\Delta t \mid \text{Distance}, V_{\text{limit}})$$
- **Teleportation Veto**: If a vehicle's observed transit time between two cameras violates physical speed limits ($\Delta t < \Delta t_{\min}$), the candidate is hard-vetoed (Score = 0.0), eliminating impossible cross-city false associations.

### Stage 7: Traffic Intelligence & Spatial Analytics
- Flow rate (vehicles per hour), vehicle density (veh/km), and corridor average speed.
- Highway Capacity Manual Level of Service (LOS) grade: A (Free Flow) through F (Severe Gridlock).
- Origin-Destination (OD) trip matrix between all camera pairs.
- Automated anomaly detection: Speeding violations, junction congestion, and security watchlist hits.

### Stage 8: Backend & Data Platform
- High-performance asynchronous FastAPI REST endpoints and OpenAPI/Swagger documentation.
- Real-time WebSocket event broadcaster (`/ws`).
- SQLite/PostGIS compatible schema with indices on cameras, observations, and journeys.

### Stage 9: Classic Ergonomic GIS Dashboard
- Single-page application built with React, TypeScript, Vite, Tailwind CSS, Leaflet, and Recharts.
- Designed with classic, calm colors: warm cream (`#F8F5EE`), hunter green (`#1E3F20`), saddle brown (`#6E472A`), and heritage navy (`#1E2C3D`).

### Stage 10: Grounded Intelligent Query Layer
- Natural language query processor that translates operator questions into deterministic SQL queries against verified database records.
- Returns grounded answers with explicit data provenance and audit citations.

### Stage 11: Deployment & Docker
- Reproducible multi-stage Docker build packaging both Python backend and Vite frontend into a self-contained container.
- `docker-compose.yml` for unified one-command orchestration.

### Stage 12: Testing & Hardening
- Complete pytest unit and integration test suite validating ANPR, tracking, spatio-temporal association, and API endpoints.
