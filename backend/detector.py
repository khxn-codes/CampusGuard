"""
Frame-differencing motion detector for CampusGuard.

This is the original lightweight backend that does NOT require any deep-learning
model or GPU. It uses Gaussian blur + absolute difference + thresholding to find
moving contours.

Use this when YOLOv8 is unavailable or for low-power devices. For production
accuracy, prefer backend/yolo_detector.py.

Returns the same interface as yolo_detector.detect_persons() so the rest of the
pipeline (zones.py, alerts.py, app.py) works without any changes:
    (motion_detected: bool, boxes: list[tuple[int, int, int, int]])
where each box is (x, y, w, h) in pixel coordinates.
"""

import cv2

# Minimum contour area in pixels². Contours smaller than this are treated as
# noise (camera sensor noise, lighting flicker, compression artefacts).
# Imported here as a module-level default; callers can override per-call.
MIN_CONTOUR_AREA = 800


def preprocess(frame):
    """
    Converts a BGR frame to a blurred grayscale image ready for absdiff.
    The Gaussian blur (21×21 kernel) suppresses high-frequency pixel noise
    so that only genuine movement generates large differences.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)


def detect_motion(prev_frame, curr_frame, min_area: int = MIN_CONTOUR_AREA):
    """
    Compares two preprocessed (grayscale + blurred) frames and returns a list
    of bounding boxes for regions that have changed significantly.

    Parameters
    ----------
    prev_frame : np.ndarray
        Preprocessed previous frame (output of preprocess()).
    curr_frame : np.ndarray
        Preprocessed current frame (output of preprocess()).
    min_area : int
        Contours with area < min_area are discarded as noise.

    Returns
    -------
    motion_detected : bool
        True if at least one contour above min_area was found.
    boxes : list[tuple[int, int, int, int]]
        List of (x, y, w, h) bounding boxes in pixel coordinates.
    """
    delta = cv2.absdiff(prev_frame, curr_frame)
    thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
    # Dilate to fill small holes inside moving regions
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []
    for contour in contours:
        if cv2.contourArea(contour) < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append((x, y, w, h))

    return len(boxes) > 0, boxes


if __name__ == "__main__":
    # Standalone test: runs the frame-diff pipeline on webcam
    import sys
    sys.path.insert(0, "..")
    from zones import draw_zone, check_zone_alert, is_inside_zone
    from config import CAMERAS

    cam_cfg = CAMERAS[0]
    zone_relative = cam_cfg["zone"]

    cap = cv2.VideoCapture(cam_cfg["source"])
    ret, first_frame = cap.read()
    prev = preprocess(first_frame)

    print("Frame-differencing detector — press Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current = preprocess(frame)
        motion, boxes = detect_motion(prev, current)

        frame = draw_zone(frame, zone_relative)
        in_zone_flags = [is_inside_zone(b, frame.shape, zone_relative) for b in boxes]
        zone_alert = any(in_zone_flags)

        for i, (x, y, w, h) in enumerate(boxes):
            color = (0, 0, 255) if in_zone_flags[i] else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        status = "ZONE ALERT" if zone_alert else ("MOTION" if motion else "CLEAR")
        color = (0, 0, 255) if zone_alert else ((0, 165, 255) if motion else (0, 255, 0))
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("CampusGuard — Frame Diff", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        prev = current

    cap.release()
    cv2.destroyAllWindows()
