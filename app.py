import streamlit as st
import pandas as pd
import plotly.express as px
import os
import cv2
from datetime import datetime, date

from backend.detector import preprocess, detect_motion
from backend.zones import draw_zone, check_zone_alert, is_inside_zone
from backend.alerts import generate_alert, draw_alert

st.set_page_config(
    page_title="CampusGuard",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------------------------------
# Backend integration
# ---------------------------------------------------------------------------
# Your backend (alerts.py) generates each alert as:
#   {"date", "time", "location", "event_type", "severity", "status"}
# This dashboard uses THOSE field names everywhere.
#
# Point this at wherever logger.py writes the CSV. Adjust the path/column
# names once logger.py actually exists and you know its real output format.
LOG_FILE_PATH = "logs/alerts_log.csv"

EXPECTED_COLUMNS = ["date", "time", "location", "event_type", "severity", "status"]


def load_alerts_from_log(path=LOG_FILE_PATH):
    """
    Loads alerts written by the backend's logger into a DataFrame.
    Falls back to an empty DataFrame (with the right columns) if the
    log file doesn't exist yet, so the dashboard doesn't crash before
    logger.py is wired up.
    """
    if not os.path.exists(path):
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[EXPECTED_COLUMNS].reset_index(drop=True)
    df.insert(0, "id", df.index + 1)  # id is generated here, not stored in the log
    return df


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

cameras = [
    {"id": "Camera 1", "location": "Main Gate", "status": "Online"},
]

camera_locations = pd.DataFrame([
    {"Camera": "Camera 1", "Location": "Main Gate",
     "lat": 26.5000, "lon": 80.2000},
])

# ---------------------------------------------------------------------------
# Sidebar / theme
# ---------------------------------------------------------------------------
st.sidebar.title("🛡️ Features")

dark_mode = st.sidebar.toggle("🌙 Dark Theme", value=False)

if st.sidebar.button("🔄 Reload alerts from log"):
    st.session_state.alerts_df = load_alerts_from_log()
    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Live Feed",
        "Multi-Camera",
        "Alerts",
        "Alert Review",
        "Campus Map",
        "Analytics",
        "Activity Feed"
    ]
)

if dark_mode:
    st.markdown("""
        <style>
        .stApp {
            background-color: #101827;
            color: #F1F5F9;
        }
        [data-testid="stSidebar"] {
            background-color: #172235;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: #F5F7FB;
            color: #172033;
        }
        [data-testid="stSidebar"] {
            background-color: #E8EEF7;
        }
        </style>
    """, unsafe_allow_html=True)


def get_alert_dataframe():
    return st.session_state.alerts_df


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if page == "Dashboard":
    st.title("🛡️ CampusGuard Dashboard")
    st.caption("AI-assisted campus security monitoring interface")

    alerts_df = get_alert_dataframe()

    if alerts_df.empty:
        st.info("No alerts logged yet. Run the backend pipeline with logger.py connected to populate this dashboard.")
    else:
        total_alerts = len(alerts_df)
        pending = len(alerts_df[alerts_df["status"] == "Unreviewed"])
        high_alerts = len(alerts_df[alerts_df["severity"] == "High"])
        online_cameras = len([c for c in cameras if c["status"] == "Online"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Alerts", total_alerts)
        col2.metric("Unreviewed Alerts", pending)
        col3.metric("High Severity", high_alerts)
        col4.metric("Cameras Online", f"{online_cameras}/{len(cameras)}")

        st.subheader("Recent Security Alerts")
        st.dataframe(
            alerts_df.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Camera Status")
    cam_cols = st.columns(len(cameras))

    for i, camera in enumerate(cameras):
        with cam_cols[i]:
            st.markdown(f"**{camera['id']}**")
            st.write(camera["location"])
            if camera["status"] == "Online":
                st.success("Online")
            else:
                st.error("Offline")

# ---------------------------------------------------------------------------
# Live Feed — runs the actual OpenCV backend pipeline
# ---------------------------------------------------------------------------
elif page == "Live Feed":
    st.title("🎥 Live Camera Feed")
    st.caption("Runs camera.py → detector.py → zones.py → alerts.py live, inside the dashboard.")

    run = st.checkbox("Start camera", key="start_camera")
    frame_placeholder = st.empty()
    alert_placeholder = st.empty()

    if run:
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            st.error("Could not open camera. Check that it's connected and not in use elsewhere.")
        else:
            ret, first_frame = cap.read()
            if not ret:
                st.error("Failed to read from camera.")
            else:
                prev = preprocess(first_frame)

                while st.session_state.get("start_camera", False):
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Failed to grab frame.")
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

                    # Streamlit needs RGB, OpenCV gives BGR
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_placeholder.image(frame_rgb, channels="RGB")

                    if alert:
                        alert_placeholder.error(
                            f"🚨 {alert['event_type']} — {alert['severity']} — {alert['time']}"
                        )
                        # NOTE: this alert only shows on screen here.
                        # Once logger.py exists, call it here to also write
                        # this alert dict to logs/alerts_log.csv.

                    prev = current

            cap.release()
    else:
        frame_placeholder.info("Camera is off. Check the box above to start.")
        st.caption("Uncheck the box or stop the Streamlit process (Ctrl+C in terminal) to release the camera.")

# ---------------------------------------------------------------------------
# Multi-Camera
# ---------------------------------------------------------------------------
elif page == "Multi-Camera":
    st.title("📹 Multi-Camera Monitoring")
    st.caption("Camera status cards — see Live Feed page for the actual video stream.")

    cam_cols = st.columns(2)

    for i, camera in enumerate(cameras):
        with cam_cols[i % 2]:
            with st.container(border=True):
                st.subheader(camera["id"])
                st.write(f"📍 Location: {camera['location']}")

                if camera["status"] == "Online":
                    st.success("Camera Online")
                else:
                    st.error("Camera Offline")

                st.info("📷 See Live Feed page for the real video stream")

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

        st.subheader(f"Alert #{selected_alert['id']}")
        st.write(f"**Event:** {selected_alert['event_type']}")
        st.write(f"**Location:** {selected_alert['location']}")
        st.write(f"**Date / Time:** {selected_alert['date']} {selected_alert['time']}")
        st.write(f"**Severity:** {selected_alert['severity']}")
        st.write(f"**Current Status:** {selected_alert['status']}")

        review_note = st.text_area(
            "Reviewer Notes",
            placeholder="Enter what you observed or verified..."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Mark Under Review"):
                idx = alerts_df[alerts_df["id"].astype(str) == selected_id].index[0]
                st.session_state.alerts_df.loc[idx, "status"] = "Under Review"
                st.session_state.activity.insert(
                    0, f"{datetime.now().strftime('%H:%M')} — Alert #{selected_id} under review"
                )
                st.success("Alert marked as Under Review.")
                st.rerun()

        with col2:
            if st.button("Resolve Alert"):
                idx = alerts_df[alerts_df["id"].astype(str) == selected_id].index[0]
                st.session_state.alerts_df.loc[idx, "status"] = "Resolved"
                st.session_state.activity.insert(
                    0, f"{datetime.now().strftime('%H:%M')} — Alert #{selected_id} resolved"
                )
                st.success("Alert marked as Resolved.")
                st.rerun()

        st.caption("Note: status changes here are session-only until logger.py supports writing status updates back to the log file.")

# ---------------------------------------------------------------------------
# Campus Map
# ---------------------------------------------------------------------------
elif page == "Campus Map":
    st.title("🗺️ Campus Camera Locations")
    st.caption("Replace them with authorized campus camera coordinates.")

    st.map(camera_locations, latitude="lat", longitude="lon")

    st.subheader("Camera Location List")
    st.dataframe(
        camera_locations[["Camera", "Location"]],
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------------------------------------------------
# Analytics
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
                title="Alert Severity"
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
                title="Event Distribution"
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
            title="Alerts by Campus Location"
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