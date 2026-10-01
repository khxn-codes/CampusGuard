import cv2
from datetime import datetime

# Configure allowed hours here (24-hour format)
ALLOWED_START_HOUR = 9    # 9:00 AM
ALLOWED_END_HOUR = 17     # 5:00 PM

# Cooldown between repeated alerts (in seconds)
ALERT_COOLDOWN = 8

_last_alert_time = None  # tracks last time an alert was triggered


def is_after_hours():
    """
    Returns True if current time is outside allowed hours.
    """
    current_hour = datetime.now().hour
    return not (ALLOWED_START_HOUR <= current_hour < ALLOWED_END_HOUR)


def generate_alert(zone_alert, motion_detected):
    """
    Combines conditions to decide alert severity.
    Returns a dict describing the event, or None if no alert.
    Applies a cooldown so the same event isn't logged repeatedly.
    """
    global _last_alert_time

    after_hours = is_after_hours()

    if not (motion_detected and zone_alert):
        return None  # no zone activity, nothing to alert on

    # Cooldown check
    now = datetime.now()
    if _last_alert_time is not None:
        elapsed = (now - _last_alert_time).total_seconds()
        if elapsed < ALERT_COOLDOWN:
            return None  # too soon since last alert

    # Decide severity
    if zone_alert and after_hours:
        severity = "High"
        event_type = "After-hours restricted zone activity"
    elif zone_alert:
        severity = "Medium"
        event_type = "Restricted zone activity"
    else:
        severity = "Low"
        event_type = "General movement"

    _last_alert_time = now

    return {
        "date": now.strftime("%d-%m-%Y"),
        "time": now.strftime("%H:%M:%S"),
        "location": "Camera 1",       # placeholder, update per camera later
        "event_type": event_type,
        "severity": severity,
        "status": "Unreviewed"
    }


def print_alert(alert):
    """
    Nicely formats and prints an alert dict to the terminal.
    """
    print("=" * 40)
    print("🚨 ALERT TRIGGERED")
    print(f"Date       : {alert['date']}")
    print(f"Time       : {alert['time']}")
    print(f"Location   : {alert['location']}")
    print(f"Event Type : {alert['event_type']}")
    print(f"Severity   : {alert['severity']}")
    print(f"Status     : {alert['status']}")
    print("=" * 40)


def draw_alert(frame, alert):
    """
    Displays alert text on the video frame.
    """
    if alert:
        text = f"ALERT: {alert['event_type']} ({alert['severity']})"
        cv2.putText(frame, text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 0, 255), 2)
    return frame


if __name__ == "__main__":
    # Standalone test: full pipeline (camera + motion + zone + alert)
    from detector import preprocess, detect_motion
    from zones import draw_zone, check_zone_alert, is_inside_zone

    cap = cv2.VideoCapture(0)
    ret, first_frame = cap.read()
    prev = preprocess(first_frame)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current = preprocess(frame)
        motion, boxes = detect_motion(prev, current)

        frame = draw_zone(frame)
        zone_alert = check_zone_alert(boxes)

        for (x, y, w, h) in boxes:
            color = (0, 0, 255) if is_inside_zone((x, y, w, h)) else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        alert = generate_alert(zone_alert, motion)
        frame = draw_alert(frame, alert)

        if alert:
            print_alert(alert)  # later, pass `alert` dict to logger.py instead

        status = "ALERT!" if alert else ("ZONE ALERT" if zone_alert else "AREA CLEAR")
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255) if alert else (0, 255, 0), 2)

        cv2.imshow("CampusGuard", frame)

        prev = current

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()