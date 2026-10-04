import cv2

# Restricted zone coordinates (x1, y1) = top-left, (x2, y2) = bottom-right
# Adjust these based on your camera's frame size and where you want the zone
from config import RESTRICTED_ZONE


def is_inside_zone(box, zone=RESTRICTED_ZONE):
    """
    Takes a motion bounding box (x, y, w, h) and checks
    if its centre point falls inside the restricted zone.
    """
    x, y, w, h = box
    cx = x + w // 2
    cy = y + h // 2

    x1, y1, x2, y2 = zone

    return x1 <= cx <= x2 and y1 <= cy <= y2


def check_zone_alert(boxes, zone=RESTRICTED_ZONE):
    """
    Given a list of motion boxes, returns True if ANY of them
    are inside the restricted zone.
    """
    for box in boxes:
        if is_inside_zone(box, zone):
            return True
    return False


def draw_zone(frame, zone=RESTRICTED_ZONE):
    """
    Draws the restricted zone rectangle on the frame for visualization.
    """
    x1, y1, x2, y2 = zone
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(frame, "RESTRICTED ZONE", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return frame


if __name__ == "__main__":
    # Standalone test: combine with detector.py
    from detector import preprocess, detect_motion

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

        status = "ZONE ALERT!" if zone_alert else "AREA CLEAR"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255) if zone_alert else (0, 255, 0), 2)

        cv2.imshow("CampusGuard - Zone Check", frame)

        prev = current

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()