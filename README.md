# CampusGuard 🛡️

An AI-assisted campus security monitoring system that uses computer vision to detect unauthorized movement in restricted zones, flag after-hours activity, and log incidents with automated snapshots. Powered by **YOLOv8 person detection**, an **OpenCV processing pipeline**, and an interactive **Streamlit dashboard in permanent Dark Mode**.

---

## Features

- **YOLOv8 Person Detection:** Real-time deep-learning detection of human intrusions (`yolov8n.pt`), eliminating false positives from lighting shifts or animals.
- **Lightweight Fallback Detector:** Frame-differencing motion detector (`backend/detector.py`) for low-resource environments.
- **Restricted Zone Enforcement:** Resolution-independent zone coordinates defined as relative fractions (0.0–1.0) in `config.py`.
- **Time-Based Rule Engine:** Automatic escalation of security events outside allowed hours (e.g. 9:00 AM – 5:00 PM).
- **3-Tier Alert Severity:**
  - 🔴 **High:** Restricted zone breach during after-hours.
  - 🟡 **Medium:** Restricted zone breach during allowed hours.
  - 🟢 **Low:** General movement detected outside restricted zones.
- **Alert Snapshots:** Automatically captures and saves evidence images (`logs/snapshots/*.jpg`) at the exact moment of an alert.
- **Permanent Sleek Dark Mode:** Enforced via `.streamlit/config.toml`, modern CSS styling, and themed dark Plotly charts.
- **7-Page Streamlit Dashboard:**
  1. **Dashboard:** High-level metrics (Total, Unreviewed, High Severity, Camera Online), recent alerts table, and active camera status.
  2. **Live Feed:** Dedicated real-time video stream with bounding boxes, restricted zone overlay, and live alert banners.
  3. **Alerts:** Advanced filtering by severity, status, event type, campus location, free-text search, and CSV export.
  4. **Alert Review:** Incident resolution workflow displaying captured alert snapshots, reviewer notes, and status updates persisted to disk.
  5. **Campus Map:** Interactive geographic map pinpointing campus camera coordinates.
  6. **Analytics:** Dark-themed Plotly charts showing severity breakdown, event distribution, and location trends.
  7. **Activity Feed:** Chronological security activity log with manual and auto-refresh capabilities.

---

## Project Structure

```
CampusGuard/
├── .streamlit/
│   └── config.toml           # Enforced Dark Mode theme configuration
├── app.py                    # Streamlit dashboard (7 pages, pure dark mode)
├── config.py                 # Centralized configuration (camera, zones, YOLO, hours)
├── logger.py                 # EventLogger with status write-back & retry buffer
├── test_run.py               # Standalone logger verification script
├── yolov8n.pt                # YOLOv8 nano model weights (~6 MB)
├── CampusGuard_PRD.md        # Comprehensive Product Requirements Document (v1.3)
├── requirements.txt          # Python dependencies (UTF-8 encoded)
├── backend/
│   ├── __init__.py
│   ├── camera.py             # OpenCV webcam capture
│   ├── yolo_detector.py      # Primary YOLOv8 person detector & bounding boxes
│   ├── detector.py           # Lightweight frame differencing fallback
│   ├── zones.py              # Relative restricted zone geometry & breach checks
│   └── alerts.py             # Severity & time-based alert logic with cooldown
└── logs/
    ├── alerts_log.csv        # 7-column CSV alert database
    └── snapshots/            # Event snapshot images (.jpg)
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/khxn-codes/CampusGuard.git
cd CampusGuard
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Launch the Streamlit web dashboard:

```bash
streamlit run app.py
```

> **Note:** Always run this command from the project root (`CampusGuard/`). `config.py` resides at root and is imported across backend modules as `from config import ...`.

1. Open your browser to `http://localhost:8501`.
2. Navigate to the **Live Feed** page from the sidebar.
3. Toggle **"Start Camera"** to initialize YOLOv8 and begin real-time detection.

---

## Configuration

All system parameters are centralized in `config.py`:

| Parameter | Default | Description |
|---|---|---|
| `CAMERAS` / `CAMERA_CONFIG` | `Camera 1` (index `0`, `Main Gate`) | Active camera device index, name, location, and zone coordinates |
| `ALLOWED_START_HOUR` | `9` (9:00 AM) | Start of normal allowed hours (24h format) |
| `ALLOWED_END_HOUR` | `17` (5:00 PM) | End of normal allowed hours (24h format) |
| `ALERT_COOLDOWN` | `5` seconds | Minimum cooldown period between consecutive logged alerts |
| `LOG_FILE_PATH` | `logs/alerts_log.csv` | Destination path for persisted security alerts |
| `YOLO_MODEL` | `yolov8n.pt` | YOLO model variant (`yolov8n`, `yolov8s`, `yolov8m`) |
| `YOLO_CONF_THRESHOLD` | `0.40` | Minimum confidence score for person detections |

---

## Alert Data Schema

Alerts are stored in `logs/alerts_log.csv` using the following 7-column schema:

| Field | Example | Description |
|---|---|---|
| `date` | `10-10-2026` | Date of the event (DD-MM-YYYY) |
| `time` | `21:47:32` | Time of the event (HH:MM:SS) |
| `location` | `Main Gate` | Camera location identifier |
| `event_type` | `After-hours restricted zone activity` | Nature of detected event |
| `severity` | `High` | Classification: `Low`, `Medium`, or `High` |
| `status` | `Unreviewed` | Review state: `Unreviewed`, `Under Review`, or `Resolved` |
| `snapshot` | `logs/snapshots/alert_20261010_214732.jpg` | Path to the captured evidence image |

---

## Team

| Module | Owner |
|---|---|
| OpenCV & YOLOv8 Backend | Shahnawaz Khan |
| Streamlit Frontend (Dark Theme) | Lakshya Mohan Bajpai |
| Data Persistence & Logging | Manya Saxena |
| Configuration & Architecture | Shweta Singh |