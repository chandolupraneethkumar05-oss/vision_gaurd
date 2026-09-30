"""Generates a comprehensive 1080p walkthrough demonstration video for VisionGuard."""
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUTPUT_VIDEO = "VisionGuard_Walkthrough_Demo.mp4"
WIDTH, HEIGHT = 1920, 1080
FPS = 24

# Palette
C_CANVAS = (248, 245, 238)
C_SURFACE = (255, 255, 255)
C_SURFACE_ALT = (241, 235, 225)
C_FOREST = (30, 63, 32)
C_BROWN = (110, 71, 42)
C_NAVY = (30, 44, 61)
C_GOLD = (196, 139, 63)
C_BORDER = (227, 219, 208)
C_TEXT_MAIN = (29, 35, 31)
C_TEXT_MUTED = (90, 101, 94)
C_RED = (155, 44, 44)

def get_font(size: int, bold: bool = False):
    try:
        font_path = "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def draw_header(draw: ImageDraw.ImageDraw, active_tab: str):
    # Header bar
    draw.rectangle([0, 0, WIDTH, 100], fill=C_SURFACE, outline=C_BORDER)
    
    # Emblem
    draw.rectangle([60, 20, 115, 75], fill=C_FOREST)
    f_emblem = get_font(28, bold=True)
    draw.text((75, 28), "VG", fill=(255, 255, 255), font=f_emblem)

    # Title
    f_title = get_font(26, bold=True)
    draw.text((135, 24), "VISIONGUARD", fill=C_FOREST, font=f_title)
    
    f_sub = get_font(14, bold=False)
    draw.text((135, 58), "AI Urban Traffic Intelligence & ANPR Platform • SIH26127", fill=C_TEXT_MUTED, font=f_sub)

    # Status Pills
    f_pill = get_font(13, bold=True)
    draw.rounded_rectangle([1380, 32, 1540, 66], radius=6, fill=(235, 243, 236), outline=(196, 220, 200))
    draw.text((1400, 40), "● SYSTEM ONLINE", fill=C_FOREST, font=f_pill)

    draw.rounded_rectangle([1560, 32, 1720, 66], radius=6, fill=C_SURFACE_ALT, outline=C_BORDER)
    draw.text((1580, 40), "30 FPS • 18ms", fill=C_BROWN, font=f_pill)

    draw.rounded_rectangle([1740, 32, 1860, 66], radius=6, fill=(235, 241, 246), outline=(197, 214, 229))
    draw.text((1760, 40), "6/6 CAMS", fill=C_NAVY, font=f_pill)

    # Tab Bar
    tabs = [
        "1. GIS Urban Map",
        "2. Live Camera Grid",
        "3. Journey Reconstructor",
        "4. Indian ANPR & Watchlist",
        "5. Traffic Intelligence",
        "6. Grounded Assistant",
        "7. System & Benchmarks"
    ]
    draw.rectangle([0, 100, WIDTH, 155], fill=C_SURFACE_ALT, outline=C_BORDER)
    x_offset = 60
    f_tab = get_font(14, bold=True)
    for t in tabs:
        is_active = active_tab in t
        if is_active:
            draw.rounded_rectangle([x_offset - 8, 108, x_offset + len(t) * 9 + 16, 147], radius=6, fill=C_FOREST)
            draw.text((x_offset, 118), t, fill=(255, 255, 255), font=f_tab)
        else:
            draw.text((x_offset, 118), t, fill=C_TEXT_MUTED, font=f_tab)
        x_offset += len(t) * 9 + 40

def make_scene_title(step_num: int, total_steps: int, title: str, subtitle: str, duration_sec: float = 3.5):
    frames = []
    total_frames = int(duration_sec * FPS)

    for i in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), C_CANVAS)
        draw = ImageDraw.Draw(img)

        # Background decorative pattern
        draw.rectangle([120, 160, WIDTH - 120, HEIGHT - 160], fill=C_SURFACE, outline=C_BORDER, width=2)
        
        # Heritage badge
        draw.rounded_rectangle([WIDTH//2 - 120, 240, WIDTH//2 + 120, 280], radius=8, fill=C_SURFACE_ALT, outline=C_BORDER)
        f_badge = get_font(14, bold=True)
        draw.text((WIDTH//2 - 95, 250), f"MODULE DEMO {step_num} OF {total_steps}", fill=C_BROWN, font=f_badge)

        # Title
        f_big = get_font(52, bold=True)
        bbox = draw.textbbox((0, 0), title, font=f_big)
        w = bbox[2] - bbox[0]
        draw.text(((WIDTH - w) // 2, 330), title, fill=C_FOREST, font=f_big)

        # Subtitle
        f_sub = get_font(22, bold=False)
        bbox_sub = draw.textbbox((0, 0), subtitle, font=f_sub)
        w_sub = bbox_sub[2] - bbox_sub[0]
        draw.text(((WIDTH - w_sub) // 2, 410), subtitle, fill=C_TEXT_MUTED, font=f_sub)

        # Progress bar
        progress = (i / float(total_frames))
        bar_w = 400
        draw.rounded_rectangle([WIDTH//2 - bar_w//2, 520, WIDTH//2 + bar_w//2, 528], radius=4, fill=C_SURFACE_ALT)
        draw.rounded_rectangle([WIDTH//2 - bar_w//2, 520, WIDTH//2 - bar_w//2 + int(bar_w * progress), 528], radius=4, fill=C_FOREST)

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames

def make_gis_scene(duration_sec: float = 4.5):
    frames = []
    total_frames = int(duration_sec * FPS)

    for i in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), C_CANVAS)
        draw = ImageDraw.Draw(img)
        draw_header(draw, "1. GIS Urban Map")

        # Map Area Card
        draw.rectangle([60, 180, 1340, 980], fill=(235, 230, 220), outline=C_BORDER, width=2)
        
        # Draw road network lines
        draw.line([200, 300, 600, 320], fill=(180, 170, 160), width=18)
        draw.line([600, 320, 1100, 480], fill=(180, 170, 160), width=18)
        draw.line([600, 320, 680, 850], fill=(180, 170, 160), width=18)
        draw.line([200, 300, 350, 750], fill=(180, 170, 160), width=18)
        draw.line([350, 750, 680, 850], fill=(180, 170, 160), width=18)
        draw.line([680, 850, 1100, 480], fill=(180, 170, 160), width=18)

        # Trajectory highlighted line
        draw.line([200, 300, 600, 320], fill=C_BROWN, width=6)
        draw.line([600, 320, 1100, 480], fill=C_BROWN, width=6)

        # Camera Markers
        cams = [
            (200, 300, "1", "CAM-01: Connaught Radial 1"),
            (600, 320, "2", "CAM-02: Barakhamba Metro"),
            (1100, 480, "4", "CAM-04: Tolstoy Marg Plaza"),
            (350, 750, "3", "CAM-03: Janpath Boulevard"),
            (680, 850, "5", "CAM-05: Sansad Marg Gate"),
        ]
        f_cam = get_font(16, bold=True)
        for cx, cy, label, name in cams:
            is_active = label == "2"
            fill_col = C_GOLD if is_active else C_FOREST
            draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=fill_col, outline=(255, 255, 255), width=3)
            draw.text((cx - 6, cy - 11), label, fill=(255, 255, 255), font=f_cam)

        # Floating Info Card on Right
        draw.rounded_rectangle([1380, 180, 1860, 980], radius=8, fill=C_SURFACE, outline=C_BORDER, width=2)
        f_card_title = get_font(20, bold=True)
        draw.text((1410, 210), "CAM-02: Barakhamba Metro", fill=C_FOREST, font=f_card_title)
        
        f_sub = get_font(14, bold=False)
        draw.text((1410, 245), "Radial-1-Ext • Speed Limit: 50 km/h", fill=C_TEXT_MUTED, font=f_sub)

        # Mini Video Stream Simulation
        draw.rectangle([1410, 290, 1830, 530], fill=(30, 32, 35))
        # Draw vehicle on stream
        car_y = 350 + int((i % 40) * 3)
        draw.rectangle([1580, car_y, 1660, car_y + 40], fill=(230, 230, 230))
        draw.rectangle([1610, car_y + 30, 1630, car_y + 36], fill=(255, 255, 255))
        draw.text((1425, 305), "● LIVE STREAM • 30 FPS", fill=(255, 255, 255), font=f_sub)

        # Metrics box
        draw.rounded_rectangle([1410, 560, 1830, 680], radius=6, fill=C_SURFACE_ALT)
        draw.text((1430, 580), "LIVE CORRIDOR FLOW", fill=C_TEXT_MUTED, font=f_sub)
        f_val = get_font(28, bold=True)
        draw.text((1430, 610), "480 vph • LOS B", fill=C_FOREST, font=f_val)

        # Callout banner at bottom
        draw.rounded_rectangle([80, 900, 1320, 960], radius=6, fill=C_FOREST)
        f_callout = get_font(18, bold=True)
        draw.text((110, 918), "CLICK ANY CAMERA TO INSPECT LIVE FEED, ROAD CONSTRAINTS & INCIDENTS", fill=(255, 255, 255), font=f_callout)

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames

def make_camera_grid_scene(duration_sec: float = 4.5):
    frames = []
    total_frames = int(duration_sec * FPS)

    for i in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), C_CANVAS)
        draw = ImageDraw.Draw(img)
        draw_header(draw, "2. Live Camera Grid")

        f_cam_t = get_font(16, bold=True)
        f_hud = get_font(13, bold=True)

        # 6 Camera Grid Layout
        coords = [
            (60, 180, 630, 540, "CAM-01: Connaught Outer Radial 1", 45),
            (690, 180, 1260, 540, "CAM-02: Barakhamba Crossing", 42),
            (1320, 180, 1860, 540, "CAM-03: Janpath Boulevard", 58),
            (60, 580, 630, 940, "CAM-04: Tolstoy Marg Plaza", 38),
            (690, 580, 1260, 940, "CAM-05: Sansad Marg Gate", 46),
            (1320, 580, 1860, 940, "CAM-06: India Gate Roundabout", 51)
        ]

        for x1, y1, x2, y2, cam_name, spd in coords:
            # Card
            draw.rectangle([x1, y1, x2, y2], fill=C_SURFACE, outline=C_BORDER, width=2)
            # Video area
            draw.rectangle([x1 + 8, y1 + 38, x2 - 8, y2 - 40], fill=(35, 38, 40))
            # Header
            draw.text((x1 + 12, y1 + 10), cam_name, fill=C_FOREST, font=f_cam_t)
            
            # Moving car simulation
            cy = y1 + 80 + int(((i * 4) + (x1 % 30)) % (y2 - y1 - 120))
            draw.rectangle([x1 + 140, cy, x1 + 220, cy + 44], fill=(220, 220, 220), outline=(20, 20, 20))
            draw.text((x1 + 145, cy + 8), "DL01AB1234", fill=(10, 10, 10), font=get_font(11, bold=True))

            # HUD
            draw.text((x1 + 16, y1 + 46), "● LIVE • 30 FPS • 1080p", fill=(255, 255, 255), font=f_hud)
            draw.text((x1 + 16, y2 - 28), f"SPEED: {spd} KM/H • FLOW: 410 VPH • LOS B", fill=C_GOLD, font=f_hud)

        # Callout banner at top
        draw.rounded_rectangle([60, 955, WIDTH - 60, 1010], radius=6, fill=C_NAVY)
        f_callout = get_font(18, bold=True)
        draw.text((90, 972), "SYNCHRONIZED REAL-TIME INGESTION: RTSP, WEBCAM & SIMULATED HIGH-DEFINITION STREAMS", fill=(255, 255, 255), font=f_callout)

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames

def make_anpr_scene(duration_sec: float = 4.5):
    frames = []
    total_frames = int(duration_sec * FPS)

    for i in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), C_CANVAS)
        draw = ImageDraw.Draw(img)
        draw_header(draw, "4. Indian ANPR & Watchlist")

        # Top Validator Card
        draw.rounded_rectangle([60, 180, WIDTH - 60, 380], radius=8, fill=C_SURFACE, outline=C_BORDER, width=2)
        f_card_t = get_font(22, bold=True)
        draw.text((90, 205), "INDIAN ANPR ENGINE & HSRP FORMAT VALIDATOR", fill=C_FOREST, font=f_card_t)

        f_sub = get_font(15, bold=False)
        draw.text((90, 245), "MoRTH-compliant regex validation across all 36 States/UTs, Bharat (BH) series, and temporal voting buffer.", fill=C_TEXT_MUTED, font=f_sub)

        # Input simulation box
        draw.rounded_rectangle([90, 290, 520, 345], radius=6, fill=C_SURFACE_ALT, outline=C_FOREST, width=2)
        f_plate = get_font(22, bold=True)
        draw.text((110, 302), "DL 01 AB 1234", fill=C_FOREST, font=f_plate)

        # Verify button
        draw.rounded_rectangle([540, 290, 720, 345], radius=6, fill=C_FOREST)
        draw.text((565, 305), "Verify Rules", fill=(255, 255, 255), font=get_font(16, bold=True))

        # Result badge
        draw.rounded_rectangle([750, 290, 1300, 345], radius=6, fill=(235, 243, 236), outline=(196, 220, 200), width=2)
        draw.text((770, 305), "✓ MORTH COMPLIANT HSRP • STANDARD PRIVATE • DELHI RTO", fill=C_FOREST, font=get_font(15, bold=True))

        # Left Column: Recent Scans
        draw.rounded_rectangle([60, 410, 940, 980], radius=8, fill=C_SURFACE, outline=C_BORDER, width=2)
        draw.text((90, 435), "LIVE ANPR OBSERVATION STREAM", fill=C_FOREST, font=f_card_t)
        
        plates = [
            ("DL 01 AB 1234", "White SUV • 96% Conf • CAM-01", "STANDARD_HSRP"),
            ("MH 12 CD 5678", "Black SUV • 94% Conf • CAM-02", "STANDARD_HSRP"),
            ("22 BH 5543 AB", "White Sedan • 97% Conf • CAM-03", "BHARAT_SERIES"),
            ("DL 1P B 8821", "Green Bus • 91% Conf • CAM-04", "COMMERCIAL_YELLOW"),
            ("HR 26 DQ 7712", "Red Motorcycle • 89% Conf • CAM-05", "TWO_WHEELER"),
        ]
        y_pl = 490
        for pl, desc, cat in plates:
            draw.rounded_rectangle([90, y_pl, 910, y_pl + 75], radius=6, fill=C_SURFACE_ALT, outline=C_BORDER)
            # HSRP badge
            draw.rounded_rectangle([110, y_pl + 14, 300, y_pl + 60], radius=4, fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.text((120, y_pl + 24), "IND", fill=(20, 40, 160), font=get_font(12, bold=True))
            draw.text((155, y_pl + 20), pl, fill=(0, 0, 0), font=get_font(16, bold=True))
            draw.text((320, y_pl + 26), desc, fill=C_TEXT_MAIN, font=get_font(14, bold=False))
            y_pl += 95

        # Right Column: Security Watchlist
        draw.rounded_rectangle([980, 410, WIDTH - 60, 980], radius=8, fill=C_SURFACE, outline=C_BORDER, width=2)
        draw.text((1010, 435), "HOT-LIST / SECURITY WATCHLIST", fill=C_BROWN, font=f_card_t)

        watchlist_items = [
            ("DL 01 AB 1234", "White Toyota Fortuner", "Highway Robbery Case #2026/89", "CRITICAL"),
            ("MH 12 CD 5678", "Black Mahindra Scorpio", "Hit-and-Run Suspect", "HIGH"),
            ("UP 16 XY 9999", "Silver Hyundai Creta", "Fake Number Plate Evasion", "MEDIUM")
        ]
        y_w = 490
        for w_pl, w_desc, w_reas, w_prio in watchlist_items:
            draw.rounded_rectangle([1010, y_w, 1830, y_w + 105], radius=6, fill=(253, 242, 242) if w_prio=="CRITICAL" else C_SURFACE_ALT, outline=C_BORDER)
            draw.text((1030, y_w + 15), f"{w_pl} • {w_desc}", fill=C_RED if w_prio=="CRITICAL" else C_BROWN, font=get_font(16, bold=True))
            draw.text((1030, y_w + 45), f"Alert: {w_reas}", fill=C_TEXT_MUTED, font=get_font(14, bold=False))
            draw.text((1030, y_w + 72), f"Priority: {w_prio}", fill=C_RED if w_prio=="CRITICAL" else C_GOLD, font=get_font(13, bold=True))
            y_w += 130

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames

def make_assistant_scene(duration_sec: float = 4.5):
    frames = []
    total_frames = int(duration_sec * FPS)

    for i in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), C_CANVAS)
        draw = ImageDraw.Draw(img)
        draw_header(draw, "6. Grounded Assistant")

        # Chat container
        draw.rounded_rectangle([60, 180, WIDTH - 60, 980], radius=8, fill=C_SURFACE, outline=C_BORDER, width=2)
        f_card_t = get_font(22, bold=True)
        draw.text((90, 205), "CONVERSATIONAL TRAFFIC INTELLIGENCE CONSOLE", fill=C_FOREST, font=f_card_t)

        f_sub = get_font(14, bold=False)
        draw.text((90, 245), "Deterministic SQL Grounding • Zero-Hallucination Guardrails • Real-Time Database Verification", fill=C_TEXT_MUTED, font=f_sub)

        # User question bubble
        draw.rounded_rectangle([800, 310, 1830, 390], radius=8, fill=C_FOREST)
        draw.text((830, 335), "Where was plate DL 01 AB 1234 last seen in the city?", fill=(255, 255, 255), font=get_font(18, bold=True))

        # Assistant response bubble
        draw.rounded_rectangle([90, 420, 1400, 680], radius=8, fill=C_SURFACE_ALT, outline=C_BORDER, width=2)
        ans_text = (
            "Vehicle DL 01 AB 1234 was most recently detected at Barakhamba Metro Crossing (CAM-02).\n\n"
            "• Recorded Transit Speed: 46.5 km/h\n"
            "• Vehicle Classification: White SUV\n"
            "• ANPR Confidence: 98%\n"
            "• Active Alert Status: WATCHLIST HIT (Robbery Case #2026/89)"
        )
        draw.text((120, 445), ans_text, fill=C_TEXT_MAIN, font=get_font(16, bold=False))

        # Citation box
        draw.rounded_rectangle([120, 580, 1370, 655], radius=6, fill=C_SURFACE, outline=C_BORDER)
        draw.text((140, 595), "DATA PROVENANCE & AUDIT CITATIONS:", fill=C_BROWN, font=get_font(13, bold=True))
        draw.text((140, 622), "TABLE: observations (ID #142) • CAMERA: CAM-02 • VERIFIED VIA SPATIAL TRANSIT GRAPH", fill=C_TEXT_MUTED, font=get_font(12, bold=False))

        # Suggested queries at bottom
        draw.text((90, 720), "SUGGESTED OPERATOR QUERIES:", fill=C_BROWN, font=get_font(15, bold=True))
        chips = [
            "Which camera junction has highest congestion?",
            "Show all speeding violations today",
            "How many active watchlist vehicles are there?"
        ]
        x_ch = 90
        for ch in chips:
            draw.rounded_rectangle([x_ch, 760, x_ch + len(ch) * 10 + 24, 805], radius=6, fill=C_SURFACE_ALT, outline=C_BORDER)
            draw.text((x_ch + 12, 773), ch, fill=C_TEXT_MAIN, font=get_font(13, bold=True))
            x_ch += len(ch) * 10 + 44

        # Input bar simulation
        draw.rounded_rectangle([90, 880, 1680, 940], radius=6, fill=C_SURFACE_ALT, outline=C_BORDER)
        draw.text((115, 900), "Ask anything about vehicles, congestion, cameras, or alerts...", fill=C_TEXT_MUTED, font=get_font(15, bold=False))
        draw.rounded_rectangle([1700, 880, 1830, 940], radius=6, fill=C_FOREST)
        draw.text((1735, 900), "Send", fill=(255, 255, 255), font=get_font(16, bold=True))

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames

def make_summary_scene(duration_sec: float = 4.5):
    frames = []
    total_frames = int(duration_sec * FPS)

    for i in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), C_CANVAS)
        draw = ImageDraw.Draw(img)

        draw.rectangle([120, 140, WIDTH - 120, HEIGHT - 140], fill=C_SURFACE, outline=C_BORDER, width=2)

        f_t = get_font(42, bold=True)
        draw.text((WIDTH//2 - 280, 200), "VISIONGUARD IS READY", fill=C_FOREST, font=f_t)

        f_sub = get_font(20, bold=False)
        draw.text((WIDTH//2 - 340, 270), "Complete AI Urban Traffic Intelligence Platform (SIH26127)", fill=C_TEXT_MUTED, font=f_sub)

        # Steps box
        draw.rounded_rectangle([200, 350, WIDTH - 200, 750], radius=8, fill=C_SURFACE_ALT, outline=C_BORDER)
        
        f_step = get_font(18, bold=True)
        f_code = get_font(16, bold=True)
        
        steps = [
            ("1. Open in Browser", "http://localhost:8000 (Full-Stack Platform Active)"),
            ("2. Interactive Swagger Docs", "http://localhost:8000/docs (Test all REST APIs)"),
            ("3. Run Test Suite", "python -m pytest tests/ (16 Tests Passing in 1.02s)"),
            ("4. Git Repository", "https://github.com/chandolupraneethkumar05-oss/vision_gaurd")
        ]
        
        y_st = 390
        for title, detail in steps:
            draw.text((240, y_st), title, fill=C_FOREST, font=f_step)
            draw.text((240, y_st + 30), detail, fill=C_BROWN, font=f_code)
            y_st += 80

        # Footer badge
        draw.rounded_rectangle([WIDTH//2 - 220, 810, WIDTH//2 + 220, 860], radius=6, fill=C_FOREST)
        draw.text((WIDTH//2 - 190, 825), "PRODUCTION READY • CLEAN GIT REPO", fill=(255, 255, 255), font=f_step)

        frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

    return frames

def build_full_video():
    print(f"Generating walkthrough demonstration video: {OUTPUT_VIDEO} ({WIDTH}x{HEIGHT} @ {FPS}fps)...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))

    scenes = [
        ("Intro", make_scene_title(1, 5, "VisionGuard Demonstration", "AI-Powered Urban Traffic Intelligence Platform (SIH26127)", 3.0)),
        ("GIS Map", make_gis_scene(5.0)),
        ("Camera Grid", make_camera_grid_scene(5.0)),
        ("ANPR Watchlist", make_anpr_scene(5.0)),
        ("Grounded Assistant", make_assistant_scene(5.0)),
        ("Summary", make_summary_scene(4.5)),
    ]

    for name, frame_list in scenes:
        print(f"  -> Rendering {name} scene ({len(frame_list)} frames)...")
        for f in frame_list:
            writer.write(f)

    writer.release()
    size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024.0 * 1024.0)
    print(f"Successfully generated {OUTPUT_VIDEO} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    build_full_video()
