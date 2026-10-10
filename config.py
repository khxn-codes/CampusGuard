"""
Centralized configuration for CampusGuard.
Change settings here instead of hunting through backend/ files.
"""

# ---------------------------------------------------------------------------
# Camera & Zone Configuration (Single Camera)
# ---------------------------------------------------------------------------
# Define the active camera settings here.
#   source: 0 for default webcam, 1 for USB webcam, or "rtsp://..." for IP cameras.
#   zone: (0.0 to 1.0) relative to frame size. e.g., (0.3, 0.3, 0.7, 0.7) is center 40%.
CAMERAS = [
    {
        "id": "Camera 1",
        "source": 0,
        "location": "Main Gate",
        "zone": (0.30, 0.30, 0.70, 0.70)
    }
]

CAMERA_CONFIG = CAMERAS[0]

# Allowed hours (24-hour format). Outside this window counts as after-hours.
ALLOWED_START_HOUR = 9    # 9:00 AM
ALLOWED_END_HOUR = 17     # 5:00 PM

# Minimum seconds between two logged alerts (prevents spamming one per frame)
ALERT_COOLDOWN = 5

# Where logger.py's EventLogger writes alerts
LOG_FILE_PATH = "logs/alerts_log.csv"

# ---------------------------------------------------------------------------
# YOLOv8 Person Detection Settings
# ---------------------------------------------------------------------------
# Which YOLOv8 model to use. Tradeoff: speed vs. accuracy.
#   yolov8n.pt  — nano   (~6 MB, fastest, lowest accuracy)
#   yolov8s.pt  — small  (~22 MB, balanced)
#   yolov8m.pt  — medium (~50 MB, more accurate, heavier)
YOLO_MODEL = "yolov8n.pt"

# Minimum confidence score (0.0–1.0) for a YOLO detection to count.
# Lower = more detections (more false positives).
# Higher = fewer detections (may miss distant/partially visible people).
YOLO_CONF_THRESHOLD = 0.40