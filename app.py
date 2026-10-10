import streamlit as st
import pandas as pd
import plotly.express as px
import os
import cv2
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh

from backend.yolo_detector import detect_persons, draw_detections, get_model
from backend.zones import draw_zone, check_zone_alert, is_inside_zone
from backend.alerts import generate_alert, draw_alert
from logger import EventLogger
from config import LOG_FILE_PATH, CAMERAS, CAMERA_CONFIG

# Initialize logger
event_logger = EventLogger()

st.set_page_config(
    page_title="CampusGuard",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------------------------------
# Global Dark Theme (Permanent Dark Mode)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Base Dark Mode Styling */
.stApp {
    background-color: #0b0f19;
    color: #f1f5f9;
}

[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1f2937;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

[data-testid="stMetricValue"] {
    color: #38bdf8 !important;
    font-weight: 700;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-weight: 500;
}

/* Containers & Cards */
div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
    background: #161f30;
    border: 1px solid #2d3748;
    border-radius: 8px;
}

/* Modern Dark Buttons */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af);
    border-color: #60a5fa;
    color: #ffffff;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
}

/* Input Fields & Selectboxes */
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border-color: #334155 !important;
}

/* Dataframe Styling */
.stDataFrame {
    border: 1px solid #1f2937;
    border-radius: 6px;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #f8fafc !important;
    letter-spacing: -0.02em;
}

hr {
    border-color: #1f2937;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Backend integration & Data Loading
# ---------------------------------------------------------------------------
EXPECTED_COLUMNS = ["date", "time", "location", "event_type", "severity", "status", "snapshot"]


def load_alerts_from_log(path=LOG_FILE_PATH):
    """
    Loads alerts written by the backend logger into a DataFrame.
    Resilient to legacy row formats or inconsistent delimiters.
    """
    if not os.path.exists(path):
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    try:
        df = pd.read_csv(path, on_bad_lines="skip")
        for col in EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[EXPECTED_COLUMNS].reset_index(drop=True)
        df.insert(0, "id", df.index + 1)
        return df
    except Exception as e:
        try:
            import csv
            rows = []
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for r in reader:
                    if not r or not any(r):
                        continue
                    while len(r) < len(EXPECTED_COLUMNS):
                        r.append("")
                    rows.append(r[:len(EXPECTED_COLUMNS)])
            if rows:
                df = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
                df.insert(0, "id", df.index + 1)
                return df
        except Exception:
            pass
        return pd.DataFrame(columns=EXPECTED_COLUMNS)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "alerts_df" not in st.session_state:
    st.session_state.alerts_df = load_alerts_from_log()

if "activity" not in st.session_state:
    st.session_state.activity = []
    for _, row in st.session_state.alerts_df.iterrows():
        st.session_state.activity.append(
            f"{row['time']} — {row['event_type']} at {row['location']}"
        )

# Camera configuration (Single Camera)
active_camera = CAMERA_CONFIG
_CAMERA_COORDS = {
    "Camera 1": {"lat": 26.5000, "lon": 80.2000},
}
camera_locations = pd.DataFrame([
    {
        "Camera": active_camera["id"],
        "Location": active_camera["location"],
        "lat": _CAMERA_COORDS.get(active_camera["id"], {}).get("lat", 26.5000),
        "lon": _CAMERA_COORDS.get(active_camera["id"], {}).get("lon", 80.2000),
    }
])

# ---------------------------------------------------------------------------
# Sidebar Navigation (Dedicated Dark Mode)
# ---------------------------------------------------------------------------
st.sidebar.title("🛡️ CampusGuard")
st.sidebar.caption("AI Campus Security System")

auto_refresh = st.sidebar.toggle("🔁 Auto-refresh (30s)", value=False)

if st.sidebar.button("🔄 Reload alerts from log"):
    st.session_state.alerts_df = load_alerts_from_log()
    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Live Feed",
        "Alerts",
        "Alert Review",
        "Campus Map",
        "Analytics",
        "Activity Feed"
    ]
)

# Auto-refresh handler for data pages
_REFRESH_PAGES = {"Dashboard", "Activity Feed", "Alerts", "Analytics"}
if auto_refresh and page in _REFRESH_PAGES:
    refresh_count = st_autorefresh(interval=30_000, key="auto_refresh")
    if refresh_count > 0:
        st.session_state.alerts_df = load_alerts_from_log()


def get_alert_dataframe(force_reload=False):
    if force_reload or "alerts_df" not in st.session_state or st.session_state.alerts_df.empty:
        st.session_state.alerts_df = load_alerts_from_log()
    return st.session_state.alerts_df


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if page == "Dashboard":
    st.title("🛡️ CampusGuard Dashboard")
    st.caption("AI-assisted campus security monitoring interface")

    alerts_df = get_alert_dataframe()

    if alerts_df.empty:
        st.info("No alerts logged yet. Run the Live Feed detection pipeline to record alerts.")
    else:
        total_alerts = len(alerts_df)
        pending = len(alerts_df[alerts_df["status"] == "Unreviewed"])
        high_alerts = len(alerts_df[alerts_df["severity"] == "High"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Alerts", total_alerts)
        col2.metric("Unreviewed Alerts", pending)
        col3.metric("High Severity", high_alerts)
        col4.metric("Camera Status", "Online (1/1)")

        st.subheader("Recent Security Alerts")
        st.dataframe(
            alerts_df.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Active Camera")
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            st.markdown(f"**{active_camera['id']}**")
        with c2:
            st.write(f"📍 **Location:** {active_camera['location']} (Source: {active_camera['source']})")
        with c3:
            st.success("🟢 Online")


# ---------------------------------------------------------------------------
# Live Feed — Dedicated Single Camera Stream
# ---------------------------------------------------------------------------
elif page == "Live Feed":
    st.title("🎥 Live Camera Feed")
    st.caption(f"Monitoring **{active_camera['id']}** ({active_camera['location']}) with YOLOv8 person detection and restricted zone monitoring.")

    cam_cfg = active_camera
    zone_relative = cam_cfg["zone"]
    cam_location = cam_cfg["location"]
    cam_id = cam_cfg["id"]

    col_ctrl, col_status = st.columns([1, 3])
    with col_ctrl:
        run = st.toggle("▶ Start Camera", key="start_camera")

    frame_placeholder = st.empty()
    alert_placeholder = st.empty()

    if run:
        with col_status:
            st.caption(f"🟢 **{cam_id}** — {cam_location} | Pipeline Active")

        with st.spinner("🤖 Loading YOLOv8 model… (one-time download ~6 MB)"):
            get_model()

        cap = cv2.VideoCapture(cam_cfg["source"])

        if not cap.isOpened():
            st.error("Could not open camera. Check that it is connected and not in use elsewhere.")
        else:
            frame_count = 0
            last_boxes = []
            last_motion = False
            last_zone_alert = False
            last_in_zone_flags = []

            while st.session_state.get("start_camera", False):
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to grab frame from camera.")
                    break

                frame_count += 1

                # ---- Detection (Every 3rd frame to optimize CPU performance) -----------
                if frame_count % 3 == 1:
                    last_motion, last_boxes = detect_persons(frame)
                    last_zone_alert = check_zone_alert(last_boxes, frame.shape, zone_relative)
                    last_in_zone_flags = [
                        is_inside_zone(b, frame.shape, zone_relative) for b in last_boxes
                    ]

                # ---- Restricted zone overlay -----------------------------
                frame = draw_zone(frame, zone_relative)

                # ---- Bounding boxes --------------------------------------
                frame = draw_detections(frame, last_boxes, last_in_zone_flags)

                # ---- Alert generation -----------------------------------
                alert = generate_alert(last_zone_alert, last_motion, location=cam_location)
                frame = draw_alert(frame, alert)

                # Convert BGR to RGB for Streamlit rendering
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                if alert:
                    snapshot_dir = os.path.join("logs", "snapshots")
                    os.makedirs(snapshot_dir, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    snapshot_path = os.path.join(snapshot_dir, f"alert_{ts}.jpg")
                    cv2.imwrite(snapshot_path, frame)
                    event_logger.log_alert(alert, snapshot_path=snapshot_path)

                    new_alert_row = {
                        "id": len(st.session_state.alerts_df) + 1,
                        "date": alert["date"],
                        "time": alert["time"],
                        "location": alert["location"],
                        "event_type": alert["event_type"],
                        "severity": alert["severity"],
                        "status": alert["status"],
                        "snapshot": snapshot_path,
                    }
                    st.session_state.alerts_df = pd.concat(
                        [st.session_state.alerts_df, pd.DataFrame([new_alert_row])],
                        ignore_index=True
                    )
                    st.session_state.activity.insert(
                        0, f"{alert['time']} — {alert['event_type']} at {alert['location']}"
                    )

                    alert_placeholder.error(
                        f"🚨 {alert['event_type']} — {alert['severity']} — {alert['time']}"
                    )

            cap.release()
    else:
        with col_status:
            st.caption(f"⚪ **{cam_id}** is idle")
        frame_placeholder.info("Camera is off. Toggle the switch above to start streaming.")


# ---------------------------------------------------------------------------
# Alerts (filtering)
# ---------------------------------------------------------------------------
elif page == "Alerts":
    st.title("🔎 Advanced Alert Filtering")

    alerts_df = get_alert_dataframe()

    if alerts_df.empty:
        st.info("No alerts available.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )

            status_filter = st.multiselect(
                "Filter by Status",
                options=sorted(alerts_df["status"].unique().tolist()),
                default=sorted(alerts_df["status"].unique().tolist())
            )

        with col2:
            event_options = sorted(alerts_df["event_type"].unique().tolist())
            event_filter = st.multiselect(
                "Filter by Event Type",
                options=event_options,
                default=event_options
            )

            location_options = sorted(alerts_df["location"].unique().tolist())
            location_filter = st.multiselect(
                "Filter by Location",
                options=location_options,
                default=location_options
            )

        search_text = st.text_input("Search alerts")

        filtered = alerts_df[
            alerts_df["severity"].isin(severity_filter)
            & alerts_df["status"].isin(status_filter)
            & alerts_df["event_type"].isin(event_filter)
            & alerts_df["location"].isin(location_filter)
        ]

        if search_text:
            searchable = (
                filtered["event_type"].astype(str)
                + " " + filtered["location"].astype(str)
            )
            filtered = filtered[
                searchable.str.contains(search_text, case=False, na=False)
            ]

        st.write(f"Showing {len(filtered)} alert(s)")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        csv_data = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Filtered Alerts",
            data=csv_data,
            file_name="campusguard_alerts.csv",
            mime="text/csv"
        )


# ---------------------------------------------------------------------------
# Alert Review
# ---------------------------------------------------------------------------
elif page == "Alert Review":
    st.title("✅ Alert Review and Resolution")

    alerts_df = get_alert_dataframe()

    if alerts_df.empty:
        st.info("There are no alerts to review.")
    else:
        alert_ids = alerts_df["id"].astype(str).tolist()

        selected_id = st.selectbox(
            "Select Alert ID",
            options=alert_ids
        )

        selected_alert = alerts_df[
            alerts_df["id"].astype(str) == selected_id
        ].iloc[0]

        col_info, col_snap = st.columns([1, 1])

        with col_info:
            st.subheader(f"Alert #{selected_alert['id']}")
            st.write(f"**Event:** {selected_alert['event_type']}")
            st.write(f"**Location:** {selected_alert['location']}")
            st.write(f"**Date / Time:** {selected_alert['date']} {selected_alert['time']}")
            st.write(f"**Severity:** {selected_alert['severity']}")
            st.write(f"**Current Status:** {selected_alert['status']}")

        with col_snap:
            snapshot_val = str(selected_alert.get("snapshot", "") or "").strip()
            if snapshot_val.lower() == "nan":
                snapshot_val = ""
            if snapshot_val and os.path.exists(snapshot_val):
                st.image(snapshot_val, caption="📸 Alert Snapshot", use_container_width=True)
            else:
                st.info("No snapshot available for this alert.")

        review_note = st.text_area(
            "Reviewer Notes",
            placeholder="Enter what you observed or verified..."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Mark Under Review"):
                idx = alerts_df[alerts_df["id"].astype(str) == selected_id].index[0]
                st.session_state.alerts_df.loc[idx, "status"] = "Under Review"
                event_logger.update_status(idx, "Under Review")  # persist to CSV
                st.session_state.activity.insert(
                    0, f"{datetime.now().strftime('%H:%M')} — Alert #{selected_id} under review"
                )
                st.success("Alert marked as Under Review.")
                st.rerun()

        with col2:
            if st.button("Resolve Alert"):
                idx = alerts_df[alerts_df["id"].astype(str) == selected_id].index[0]
                st.session_state.alerts_df.loc[idx, "status"] = "Resolved"
                event_logger.update_status(idx, "Resolved")  # persist to CSV
                st.session_state.activity.insert(
                    0, f"{datetime.now().strftime('%H:%M')} — Alert #{selected_id} resolved"
                )
                st.success("Alert marked as Resolved.")
                st.rerun()

        st.caption("Status changes are saved to the log file and persist across sessions.")


# ---------------------------------------------------------------------------
# Campus Map
# ---------------------------------------------------------------------------
elif page == "Campus Map":
    st.title("🗺️ Campus Camera Location")
    st.caption("Monitoring point location on campus.")

    st.map(camera_locations, latitude="lat", longitude="lon")

    st.subheader("Camera Location Details")
    st.dataframe(
        camera_locations[["Camera", "Location"]],
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------------------------
# Analytics (Themed in Dark Mode)
# ---------------------------------------------------------------------------
elif page == "Analytics":
    st.title("📊 Security Analytics")

    alerts_df = get_alert_dataframe()

    if alerts_df.empty:
        st.info("No alert data available for analytics.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Alerts by Severity")
            severity_counts = (
                alerts_df["severity"]
                .value_counts()
                .rename_axis("Severity")
                .reset_index(name="Count")
            )
            fig1 = px.bar(
                severity_counts,
                x="Severity",
                y="Count",
                color="Severity",
                title="Alert Severity Breakdown",
                color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"},
                template="plotly_dark"
            )
            fig1.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F1F5F9")
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Alerts by Event Type")
            event_counts = (
                alerts_df["event_type"]
                .value_counts()
                .rename_axis("Event")
                .reset_index(name="Count")
            )
            fig2 = px.pie(
                event_counts,
                names="Event",
                values="Count",
                title="Event Distribution",
                template="plotly_dark",
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            fig2.update_layout(
                paper_bgcolor="#111827",
                font=dict(color="#F1F5F9")
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Alerts by Location")
        location_counts = (
            alerts_df["location"]
            .value_counts()
            .rename_axis("Location")
            .reset_index(name="Count")
        )
        fig3 = px.bar(
            location_counts,
            x="Location",
            y="Count",
            title="Alerts by Campus Location",
            template="plotly_dark",
            color_discrete_sequence=["#38BDF8"]
        )
        fig3.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#F1F5F9")
        )
        st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# Activity Feed
# ---------------------------------------------------------------------------
elif page == "Activity Feed":
    st.title("🔴 Security Activity Feed")
    st.caption(
        "This feed is built from the alert log. Use 'Reload alerts from log' "
        "in the sidebar to pull in new events once your backend is logging live."
    )

    st.subheader("Latest Activity")

    if not st.session_state.activity:
        st.info("No activity yet.")
    else:
        for item in st.session_state.activity:
            st.info(item)

    if st.button("🔄 Refresh Feed"):
        st.rerun()