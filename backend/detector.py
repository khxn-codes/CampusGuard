import cv2

def preprocess(frame):
    """
    Converts frame to grayscale and applies blur
    to reduce noise before comparison.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    return blurred


def detect_motion(prev_frame, current_frame, min_area=800):
    """
    Compares two preprocessed frames and returns:
    - motion_detected (True/False)
    - list of bounding boxes (x, y, w, h) for detected movement
    """
    diff = cv2.absdiff(prev_frame, current_frame)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    boxes = []

    for c in contours:
        if cv2.contourArea(c) < min_area:
            continue  # ignore small/noisy movement

        motion_detected = True
        x, y, w, h = cv2.boundingRect(c)
        boxes.append((x, y, w, h))

    return motion_detected, boxes


if __name__ == "__main__":
    # Quick standalone test using the webcam
    cap = cv2.VideoCapture(0)
    ret, first_frame = cap.read()
    prev = preprocess(first_frame)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current = preprocess(frame)
        motion, boxes = detect_motion(prev, current)

        for (x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        status = "MOVEMENT DETECTED" if motion else "AREA CLEAR"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255) if motion else (0, 255, 0), 2)

        cv2.imshow("CampusGuard - Motion Detection", frame)

        prev = current  # update previous frame

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()