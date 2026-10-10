import cv2

def get_absolute_zone(frame_shape, zone_relative):
    """
    Converts relative zone coordinates (0.0 to 1.0) into absolute pixel coordinates
    based on the current frame's dimensions.
    """
    h, w = frame_shape[:2]
    rx1, ry1, rx2, ry2 = zone_relative
    return int(rx1 * w), int(ry1 * h), int(rx2 * w), int(ry2 * h)


def is_inside_zone(box, frame_shape, zone_relative):
    """
    Takes a bounding box (x, y, w, h) and checks if its center point
    falls inside the dynamically calculated restricted zone.
    """
    x, y, w, h = box
    cx = x + w // 2
    cy = y + h // 2

    x1, y1, x2, y2 = get_absolute_zone(frame_shape, zone_relative)

    return x1 <= cx <= x2 and y1 <= cy <= y2


def check_zone_alert(boxes, frame_shape, zone_relative):
    """
    Given a list of bounding boxes, returns True if ANY of them
    are inside the restricted zone.
    """
    for box in boxes:
        if is_inside_zone(box, frame_shape, zone_relative):
            return True
    return False


def draw_zone(frame, zone_relative):
    """
    Draws the restricted zone rectangle on the frame for visualization.
    """
    x1, y1, x2, y2 = get_absolute_zone(frame.shape, zone_relative)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(
        frame, "RESTRICTED ZONE", (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
    )
    return frame