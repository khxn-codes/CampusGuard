"""
Centralized configuration for CampusGuard.
Change settings here instead of hunting through backend/ files.

NOTE: adding this file alone doesn't change anything yet — backend/zones.py,
backend/alerts.py, and logger.py still have these same values hardcoded
locally. See the bottom of this file for exactly what to change in each to
actually use these settings instead.
"""

# Camera
CAMERA_INDEX = 0

# Restricted zone, in pixel coordinates: (x1, y1) top-left, (x2, y2) bottom-right.
# Matches backend/zones.py's current RESTRICTED_ZONE exactly.
# NOTE: these are fixed pixel values, so they assume whatever resolution
# your camera actually captures at (commonly 640x480) — if you change
# cameras or resolution, these will need re-tuning.
RESTRICTED_ZONE = (200, 150, 450, 400)  # x1, y1, x2, y2

# Allowed hours (24-hour format). Outside this window counts as after-hours.
ALLOWED_START_HOUR = 9    # 9:00 AM
ALLOWED_END_HOUR = 17     # 5:00 PM

# Minimum seconds between two logged alerts (prevents spamming one per frame)
ALERT_COOLDOWN = 5

# Where logger.py's EventLogger writes alerts
LOG_FILE_PATH = "logs/alerts_log.csv"


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