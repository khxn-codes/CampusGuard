"""
Camera capture utilities for CampusGuard.

Reads camera sources from config.py (CAMERAS list) so changing a camera
index or switching to an RTSP stream only requires an edit in config.py.
"""

import cv2
from config import CAMERAS


def open_camera(cam_cfg: dict) -> cv2.VideoCapture:
    """
    Opens a VideoCapture for the given camera config dict.

    Parameters
    ----------
    cam_cfg : dict
        One entry from the CAMERAS list in config.py.
        Must have a 'source' key (int index or RTSP URL string).

    Returns
    -------
    cv2.VideoCapture or None if the camera could not be opened.
    """
    cap = cv2.VideoCapture(cam_cfg["source"])
    if not cap.isOpened():
        print(f"[CAMERA] Error: Could not open {cam_cfg['id']} (source={cam_cfg['source']}).")
        return None
    print(f"[CAMERA] Opened {cam_cfg['id']} at {cam_cfg['location']} (source={cam_cfg['source']}).")
    return cap


def start_camera(cam_index: int = 0):
    """
    Opens the camera at position cam_index in the CAMERAS config list,
    displays the live feed, and closes cleanly when 'q' is pressed.

    Parameters
    ----------
    cam_index : int
        Index into the CAMERAS list (not the OpenCV device index).
    """
    if cam_index >= len(CAMERAS):
        print(f"[CAMERA] Error: CAMERAS list has {len(CAMERAS)} entries; index {cam_index} is out of range.")
        return

    cam_cfg = CAMERAS[cam_index]
    cap = open_camera(cam_cfg)
    if cap is None:
        return

    window_title = f"CampusGuard — {cam_cfg['id']} ({cam_cfg['location']})"

    while True:
        ret, frame = cap.read()

        if not ret:
            print("[CAMERA] Error: Failed to grab frame.")
            break

        cv2.imshow(window_title, frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_camera(0)