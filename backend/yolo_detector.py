"""
YOLOv8-based person detector for CampusGuard.

Replaces the frame-differencing approach with a neural network that detects
humans specifically, eliminating false positives from lighting changes,
shadows, and camera noise.

Model is downloaded automatically on first run (~6 MB for yolov8n.pt).
Subsequent runs load from the local Ultralytics cache.
"""

import cv2
from ultralytics import YOLO

from config import YOLO_MODEL, YOLO_CONF_THRESHOLD

_PERSON_CLASS = 0  # COCO class index for 'person'

# Module-level singleton — model is loaded once and reused every frame.
_model: YOLO | None = None


def get_model() -> YOLO:
    """Lazy-loads the YOLO model the first time detection is called."""
    global _model
    if _model is None:
        _model = YOLO(YOLO_MODEL)
    return _model


def detect_persons(frame, conf_threshold: float = YOLO_CONF_THRESHOLD):
    """
    Runs YOLOv8 inference on a BGR frame and returns person detections.

    Returns the same interface as backend/detector.py's detect_motion() so
    zones.py and alerts.py work without any changes:
        (motion_detected: bool, boxes: list[tuple[int, int, int, int]])
    where each box is (x, y, w, h) in pixel coordinates.

    Parameters
    ----------
    frame : np.ndarray
        Raw BGR frame from OpenCV.
    conf_threshold : float
        Minimum confidence to count a detection (0–1). Default from config.py.
    """
    model = get_model()
    # Speed optimizations:
    # 1. imgsz=320 (downscales image before inference; 4x faster than default 640)
    # 2. classes=[0] (only look for persons, saves time in post-processing/NMS)
    results = model(frame, verbose=False, imgsz=320, classes=[_PERSON_CLASS])[0]

    boxes = []
    for box in results.boxes:
        conf = float(box.conf[0])

        if conf < conf_threshold:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        boxes.append((x1, y1, x2 - x1, y2 - y1))  # convert to (x, y, w, h)

    return len(boxes) > 0, boxes


def draw_detections(frame, boxes, in_zone_flags: list[bool] | None = None):
    """
    Draws YOLO person bounding boxes and confidence labels on the frame.

    Parameters
    ----------
    frame : np.ndarray
        BGR frame to draw on (modified in-place).
    boxes : list[tuple[int, int, int, int]]
        List of (x, y, w, h) bounding boxes from detect_persons().
    in_zone_flags : list[bool] | None
        Per-box flag indicating whether the person is inside the restricted
        zone. If provided, zone-breaching boxes are drawn red; others green.
    """
    for i, (x, y, w, h) in enumerate(boxes):
        in_zone = in_zone_flags[i] if in_zone_flags else False
        color = (0, 0, 255) if in_zone else (0, 255, 0)
        label = "Person ⚠ ZONE" if in_zone else "Person"

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        # Background rectangle for legible label text
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(frame, (x, y - th - 6), (x + tw + 4, y), color, -1)
        cv2.putText(
            frame, label, (x + 2, y - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2
        )

    return frame


if __name__ == "__main__":
    # Standalone test: runs the full YOLO pipeline on webcam
    import sys
    sys.path.insert(0, "..")  # allow `from config import ...` when run from backend/
    from zones import draw_zone, check_zone_alert, is_inside_zone

    cap = cv2.VideoCapture(0)
    print("YOLOv8 person detector — press Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        motion, boxes = detect_persons(frame)
        frame = draw_zone(frame)

        in_zone_flags = [is_inside_zone(b) for b in boxes]
        frame = draw_detections(frame, boxes, in_zone_flags)

        zone_alert = any(in_zone_flags)
        status = "🚨 ZONE ALERT" if zone_alert else ("PERSON DETECTED" if motion else "AREA CLEAR")
        color = (0, 0, 255) if zone_alert else ((0, 165, 255) if motion else (0, 255, 0))
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("CampusGuard — YOLOv8", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
