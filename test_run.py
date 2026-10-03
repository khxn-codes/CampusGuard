# Quick standalone test for logger.py
from logger import EventLogger

logger = EventLogger()

print("Testing the logger file...")

logger.log_event(
    date_str="01-10-2026",
    time_str="20:15:00",
    location="Camera 1",
    event_type="After-hours restricted zone activity",
    severity="High",
    status="Unreviewed"
)

print("Test complete! Check logs/alerts_log.csv")