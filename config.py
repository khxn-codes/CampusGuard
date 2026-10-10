"""
Centralized configuration for CampusGuard.
Change settings here instead of hunting through backend/ files.

NOTE: adding this file alone doesn't change anything yet — backend/zones.py,
backend/alerts.py, and logger.py still have these same values hardcoded
locally. See the bottom of this file for exactly what to change in each to
actually use these settings instead.
"""

# ---------------------------------------------------------------------------
# Cameras & Zones (Phase 3 Multi-Camera Support)
# ---------------------------------------------------------------------------
# Define all cameras here. Each camera needs an ID, a video source, a location
# name, and a specific relative restricted zone (x1, y1, x2, y2).
#   source: 0 for default webcam, 1 for USB webcam, or "rtsp://..." for IP cameras.
#   zone: (0.0 to 1.0) relative to frame size. e.g., (0.3, 0.3, 0.7, 0.7) is center 40%.
CAMERAS = [
    {
        "id": "Camera 1",
        "source": 0,
        "location": "Main Gate",
        "zone": (0.30, 0.30, 0.70, 0.70)
    },
    # To add a second camera, uncomment and configure below:
    # {
    #     "id": "Camera 2",
    #     "source": 1,
    #     "location": "Back Door",
    #     "zone": (0.10, 0.10, 0.90, 0.90)
    # }
]

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
#   yolov8n.pt  — nano   (~6 MB,  fastest, lowest accuracy)
#   yolov8s.pt  — small  (~22 MB, balanced)
#   yolov8m.pt  — medium (~50 MB, more accurate, heavier)
YOLO_MODEL = "yolov8n.pt"

# Minimum confidence score (0.0–1.0) for a YOLO detection to count.
# Lower = more detections (more false positives).
# Higher = fewer detections (may miss distant/partially visible people).
YOLO_CONF_THRESHOLD = 0.40


# ---------------------------------------------------------------------------
# To actually wire this in (optional — nothing breaks if you don't):
#
# backend/zones.py — replace:
#     RESTRICTED_ZONE = (200, 150, 450, 400)
#   with:
#     from config import RESTRICTED_ZONE
#
# backend/alerts.py — replace:
#     ALLOWED_START_HOUR = 9
#     ALLOWED_END_HOUR = 17
#     ALERT_COOLDOWN = 8
#   with:
#     from config import ALLOWED_START_HOUR, ALLOWED_END_HOUR, ALERT_COOLDOWN
#
# logger.py — replace:
#     def __init__(self, log_file="logs/alerts_log.csv"):
#   with:
#     from config import LOG_FILE_PATH
#     def __init__(self, log_file=LOG_FILE_PATH):
# ---------------------------------------------------------------------------