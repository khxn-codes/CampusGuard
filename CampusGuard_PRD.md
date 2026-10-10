# CampusGuard — Product Requirements Document (PRD)

**Version:** 1.3  
**Date:** October 2026  
**Status:** Active Development  
**Team:** Shahnawaz Khan · Lakshya Mohan Bajpai · Manya Saxena · Shweta Singh

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| 1.0 | Oct 2026 | Initial PRD — full v1.0 scope, known bugs documented |
| 1.1 | Oct 2026 | All v1.0 bugs resolved; Phase 2 & 4 features implemented; `detector.py` added; `requirements.txt` fixed; `camera.py` and `app.py` wired to `config.py` |
| 1.2 | Oct 2026 | Phase 3 multi-camera worker exploration |
| 1.3 | Oct 2026 | Multi-camera support completely removed; dedicated single-camera pipeline enforced; Light mode completely removed with permanent dark mode theme enforced |

---

## 1. Executive Summary

CampusGuard is an AI-assisted campus security monitoring system that uses computer vision to detect unauthorized movement in restricted zones and flag after-hours activity. It provides a real-time Streamlit dashboard for security personnel to monitor live camera feeds, review and resolve alerts, analyze trends, and track activity across campus — all without requiring specialized hardware beyond a standard webcam.

---

## 2. Problem Statement

Campus security teams face growing challenges in monitoring large areas with limited personnel. Key pain points include:

- **Manual surveillance fatigue** — Security guards cannot continuously watch multiple camera feeds effectively.
- **Delayed incident response** — Incidents in restricted zones (labs, server rooms, admin offices) are often discovered after the fact via footage review.
- **No structured alert history** — Incidents are logged inconsistently (or not at all), making pattern analysis impossible.
- **High cost of dedicated hardware** — Commercial CCTV systems with AI analytics are expensive and require proprietary infrastructure.

CampusGuard addresses these with a low-cost, software-first approach running on commodity hardware.

---

## 3. Goals & Success Metrics

| Goal | Success Metric |
|---|---|
| Detect movement in restricted zones in real-time | Alert generated within 1 frame-cycle (~33ms at 30 fps) of breach |
| Reduce false positive alert spam | Cooldown mechanism limits alerts to ≤1 per 5 seconds per zone |
| Give security staff a usable review interface | Alert review/resolution accessible within 2 clicks from dashboard |
| Persist all alert data for audit trails | 100% of alerts written to CSV log with correct schema |
| Support after-hours threat escalation | After-hours alerts correctly classified as `High` severity |

---

## 4. Scope — Current Version (v1.3)

### 4.1 In Scope (Implemented & Working)

- Single-camera live feed via OpenCV (default webcam, index 0, configured in `config.py`)
- **YOLOv8 person detection** (replaces frame-differencing; `yolov8n.pt` default model)
- Frame-differencing motion detection as a lightweight fallback (`backend/detector.py`)
- Restricted zone definition via **relative coordinates** (0.0–1.0 fractions of frame size) in `config.py` — resolution-independent
- Alert severity classification:
  - **High** — zone breach during after-hours
  - **Medium** — zone breach during allowed hours
  - **Low** — general motion, not in zone (now fully reachable)
- Alert cooldown (configurable, default 5 seconds)
- CSV-based alert persistence (`logs/alerts_log.csv`) with retry buffering
- **Alert snapshots** — JPEG saved to `logs/snapshots/` on each alert; displayed in Alert Review
- **Status write-back** — `EventLogger.update_status()` persists status changes to CSV
- Streamlit dashboard with 7 pages: Dashboard, Live Feed, Alerts, Alert Review, Campus Map, Analytics, Activity Feed
- **Permanent Dark Mode** — custom high-contrast dark theme configured in `.streamlit/config.toml`, injected CSS, and Plotly charts (Light mode completely removed)
- Auto-refresh (30s) for Dashboard, Alerts, Analytics, Activity Feed pages
- Alert filtering by severity, status, event type, location
- Free-text alert search
- CSV export of filtered alerts
- Plotly analytics charts (severity bar, event type pie, location bar) with dark theme styling
- `st.map` camera location viewer
- All settings centralized in `config.py`; no duplicate definitions in `app.py`

### 4.2 Out of Scope (v1.3)

- Multi-camera live streams (completely out of scope; dedicated single-camera architecture)
- Light mode / theme toggle (completely removed; dark theme only)
- User authentication / role-based access
- Push notifications (email/SMS/webhook)
- Face detection / anonymization
- Pose estimation
- Object left behind detection
- Cloud hosting / remote access
- Database backend (still CSV-based)

---

## 5. User Personas

### 5.1 Campus Security Officer
- **Goal:** Monitor live feed, receive instant alerts, review and resolve incidents quickly.
- **Tech comfort:** Low–Medium. Needs a simple, self-explanatory UI.
- **Pain point:** Cannot watch multiple screens simultaneously; needs automated flagging.

### 5.2 Security Supervisor / Manager
- **Goal:** Review alert history, identify patterns, generate reports, verify staff responsiveness.
- **Tech comfort:** Medium. Comfortable with dashboards and data tables.
- **Pain point:** No historical data or trend visibility with current manual process.

### 5.3 IT / System Administrator
- **Goal:** Deploy, configure, and maintain the system. Adjust zone coordinates, camera indices, allowed hours.
- **Tech comfort:** High.
- **Pain point:** Needs configuration to be centralized and well-documented.

---

## 6. Functional Requirements

### 6.1 Backend Pipeline

| ID | Requirement | Priority | Status |
|---|---|---|---|
| BE-01 | System SHALL capture frames from a configurable camera index | P0 | ✅ Done |
| BE-02 | Motion detection SHALL use frame differencing with Gaussian blur preprocessing | P0 | ✅ Done (`backend/detector.py`) |
| BE-03 | Contours below `min_area=800px²` SHALL be ignored to reduce noise | P0 | ✅ Done |
| BE-04 | Restricted zone SHALL be defined as relative (0.0–1.0) coordinates in `config.py` | P0 | ✅ Done |
| BE-05 | Zone breach SHALL be detected by checking if a contour's center point falls within the zone | P0 | ✅ Done |
| BE-06 | `generate_alert()` SHALL apply a cooldown (default 5s) before emitting a new alert | P0 | ✅ Done |
| BE-07 | Alert severity SHALL be `High` (zone + after-hours), `Medium` (zone only), `Low` (general motion) | P0 | ✅ Done |
| BE-08 | Each alert SHALL carry: `date`, `time`, `location`, `event_type`, `severity`, `status` | P0 | ✅ Done |
| BE-09 | Alerts SHALL be appended to a CSV log with retry buffering on write failure | P0 | ✅ Done |
| BE-10 | YOLOv8 person detector SHALL replace frame-differencing for primary detection | P1 | ✅ Done (`backend/yolo_detector.py`) |
| BE-11 | Snapshot JPEG SHALL be saved on each alert trigger | P1 | ✅ Done |

### 6.2 Dashboard (Frontend)

| ID | Requirement | Priority | Status |
|---|---|---|---|
| FE-01 | Dashboard SHALL display total alerts, unreviewed count, high severity count, and camera online count | P0 | ✅ Done |
| FE-02 | Live Feed page SHALL render the OpenCV pipeline output as a real-time image stream in the browser | P0 | ✅ Done |
| FE-03 | Restricted zone SHALL be visually overlaid on the live frame | P0 | ✅ Done |
| FE-04 | Motion bounding boxes SHALL be colored red (inside zone) or green (outside zone) | P0 | ✅ Done |
| FE-05 | Alert overlay text SHALL appear on frame when an alert is active | P0 | ✅ Done |
| FE-06 | Alerts page SHALL support filtering by severity, status, event type, location, and free-text search | P1 | ✅ Done |
| FE-07 | Filtered alerts SHALL be exportable as CSV | P1 | ✅ Done |
| FE-08 | Alert Review page SHALL allow status update to "Under Review" or "Resolved" (persisted to CSV) | P1 | ✅ Done |
| FE-09 | Analytics page SHALL show severity distribution, event type distribution, and location distribution charts | P1 | ✅ Done |
| FE-10 | Campus Map page SHALL show camera locations on an interactive map | P2 | ✅ Done |
| FE-11 | Activity Feed SHALL show a chronological list of all logged events | P2 | ✅ Done |
| FE-12 | Dashboard SHALL use a permanent high-contrast Dark Mode theme (Light mode completely removed) | P2 | ✅ Done |
| FE-13 | Alert Review page SHALL display snapshot image when available | P1 | ✅ Done |
| FE-14 | Dashboard SHALL auto-refresh on a configurable interval (sidebar toggle) | P2 | ✅ Done |

### 6.3 Configuration

| ID | Requirement | Priority | Status |
|---|---|---|---|
| CFG-01 | All tunable parameters SHALL live in `config.py` | P0 | ✅ Done |
| CFG-02 | Backend modules SHALL import settings from `config.py` (no local hardcoding) | P1 | ✅ Done |
| CFG-03 | `app.py` SHALL read camera list from `config.py` CAMERAS (no hardcoded camera dicts) | P1 | ✅ Done |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Pipeline SHALL process at ≥15 fps on a standard laptop CPU |
| **Reliability** | Logger SHALL not drop alerts on transient file errors (retry buffer) |
| **Usability** | Dashboard SHALL be navigable without training; all pages accessible from sidebar |
| **Portability** | System SHALL run on Windows, macOS, and Linux with the same codebase |
| **Maintainability** | All settings centralized in `config.py`; no magic numbers in business logic |
| **Compatibility** | SHALL work with OpenCV-compatible USB and built-in webcams |

---

## 8. Known Bugs & Technical Debt

| ID | Issue | Severity | Status |
|---|---|---|---|
| BUG-01 | `Low` severity alert branch was unreachable | Medium | ✅ **Fixed** — separate `else` path in `generate_alert()` now emits Low-severity "General movement" alerts |
| BUG-02 | Alert status changes were session-only, not persisted to CSV | High | ✅ **Fixed** — `EventLogger.update_status()` writes status back to CSV; called from both "Mark Under Review" and "Resolve Alert" buttons |
| BUG-03 | `RESTRICTED_ZONE` used hardcoded pixel coords | Medium | ✅ **Fixed** — zone expressed as (0.0–1.0) relative fractions in `config.py`; `zones.py` converts to pixels per frame |
| BUG-04 | `LOG_FILE_PATH` was defined twice (once in `config.py`, again in `app.py`) | Low | ✅ **Fixed** — `app.py` now imports `LOG_FILE_PATH` from `config.py` only |
| BUG-05 | `requirements.txt` saved in UTF-16 — may fail `pip install` on non-Windows machines | Low | ✅ **Fixed** — re-saved as UTF-8; `ultralytics` added as a dependency |
| BUG-06 | `backend/detector.py` missing — referenced in architecture diagram but not created | Medium | ✅ **Fixed** — frame-differencing detector added |
| BUG-07 | `camera.py` hardcoded `VideoCapture(0)` instead of reading from `CAMERAS` config | Low | ✅ **Fixed** — `camera.py` now reads camera source from `config.CAMERAS` |
| BUG-08 | `app.py` Live Feed called `check_zone_alert`, `is_inside_zone`, `draw_zone` without `zone_relative` arg | High | ✅ **Fixed** — all three calls now pass `zone_relative` from `CAMERAS[0]` config |

---

## 9. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit (app.py)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │Dashboard │ │Live Feed │ │ Alerts   │ │Analytics  │  │
│  └──────────┘ └────┬─────┘ └──────────┘ └───────────┘  │
│                    │ (runs pipeline in-process)          │
└────────────────────┼────────────────────────────────────┘
                     │
         ┌───────────▼────────────┐
         │     OpenCV Backend     │
         │  camera.py (capture)   │
         │  yolo_detector.py ◄──┐ │  ← primary detector
         │  detector.py (diff)  │ │  ← lightweight fallback
         │  zones.py (zone check)│ │
         │  alerts.py (severity) │ │
         └───────────┬────────────┘
                     │ alert dict + snapshot path
         ┌───────────▼────────────┐
         │      logger.py         │
         │  EventLogger → CSV     │
         │  update_status() ←────── Alert Review UI
         └───────────┬────────────┘
                     │
         logs/alerts_log.csv ──► Dashboard reads on load / reload
         logs/snapshots/*.jpg ──► Alert Review displays snapshot
```

---

## 10. Future Scope

### Phase 2 — Stability & Completeness *(partially complete)*

| Feature | Description | Priority | Status |
|---|---|---|---|
| **Status write-back** | `EventLogger.update_status()` writes status changes back to CSV | P0 | ✅ Done |
| **Reachable Low-severity alerts** | Separate alert path for general motion (not in zone) | P1 | ✅ Done |
| **Relative zone coordinates** | Express zone as (0.0–1.0) fractions of frame width/height | P1 | ✅ Done |
| **Config deduplication** | Remove `LOG_FILE_PATH` duplicate from `app.py` | P1 | ✅ Done |
| **Auto-reload on new alerts** | `st_autorefresh` on Dashboard/Alerts/Analytics/Activity Feed | P2 | ✅ Done |

### Phase 3 — Streamlined Single-Camera Architecture & UI Hardening *(Completed)*

| Feature | Description | Status |
|---|---|---|
| **Single-camera dedicated pipeline** | Removed multi-camera thread overhead; focused on low-latency, robust single-camera streaming | ✅ Done |
| **Permanent Dark Theme** | Enforced dark theme across `.streamlit/config.toml`, custom CSS, and Plotly charts; light mode retired | ✅ Done |
| **Clean navigation structure** | Streamlined 7-page dashboard navigation without multi-camera placeholders | ✅ Done |

### Phase 4 — AI & Detection Upgrades *(partially complete)*

| Feature | Description | Status |
|---|---|---|
| **Person detection** | YOLOv8n replaces frame-differencing; filters alerts to human class only | ✅ Done |
| **Face detection / anonymization** | Blur faces in logged snapshots | Planned |
| **Pose estimation** | Detect aggressive postures or falls using MediaPipe Pose | Planned |
| **Object left behind** | Alert if an object remains stationary in a zone for >N minutes | Planned |
| **Crowd density estimation** | Count people; alert when density exceeds threshold | Planned |

### Phase 5 — Notifications & Integrations

| Feature | Description |
|---|---|
| **Email alerts** | Send SMTP email on High-severity alert with frame snapshot attached |
| **SMS / WhatsApp** | Twilio integration for on-call security officer paging |
| **Webhook / Slack** | POST alert payload to a configurable webhook (Slack, Teams, Discord) |
| **Alert snapshot** | Already implemented — JPEG saved at moment of alert, shown in Alert Review |

### Phase 6 — Authentication & Access Control

| Feature | Description |
|---|---|
| **Login system** | Username/password auth (Streamlit-Authenticator or custom) |
| **Role-based access** | `Viewer` (read-only), `Reviewer` (can change status), `Admin` (config + user management) |
| **Audit log** | Track who reviewed/resolved which alert and when |

### Phase 7 — Deployment & Scalability

| Feature | Description |
|---|---|
| **Docker containerization** | `Dockerfile` + `docker-compose.yml` for one-command deployment |
| **Database backend** | Replace CSV with SQLite (local) or PostgreSQL (multi-node) |
| **REST API** | FastAPI layer so dashboard and external tools can read/write alerts |
| **Cloud deployment** | Deploy on GCP / AWS with RTSP camera stream ingestion |
| **Mobile companion app** | React Native or Flutter app for on-the-go alert review |

### Phase 8 — Analytics & Reporting

| Feature | Description |
|---|---|
| **Time-series heatmap** | Hour-of-day × day-of-week alert frequency heatmap |
| **Zone-specific analytics** | Per-zone breach counts and peak breach times |
| **Automated PDF reports** | Weekly/monthly security summary report generation |
| **Anomaly detection** | Flag statistically unusual alert spikes vs. historical baseline |

---

## 11. Team & Module Ownership

| Module | Owner | Files |
|---|---|---|
| OpenCV backend | Shahnawaz Khan | `backend/camera.py`, `backend/detector.py`, `backend/yolo_detector.py`, `backend/zones.py`, `backend/alerts.py` |
| Streamlit frontend | Lakshya Mohan Bajpai | `app.py` |
| Logger / persistence | Manya Saxena | `logger.py`, `logs/` |
| Configuration | Shweta Singh | `config.py` |

---

## 12. Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web dashboard framework |
| `streamlit-autorefresh` | Auto-refresh dashboard pages on a timer |
| `opencv-python` | Camera capture + computer vision |
| `ultralytics` | YOLOv8 person detection model |
| `pandas` | Alert data manipulation |
| `plotly` | Interactive analytics charts |
| `python-dateutil` | Date parsing utilities |

---

*Document maintained by the CampusGuard team. Update version and date on each significant revision.*
