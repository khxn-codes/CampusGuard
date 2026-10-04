import csv
import os

from config import LOG_FILE_PATH
class EventLogger:
    """
    Writes alert events to a CSV log.
    Column names and default path are matched to what app.py expects:
    logs/alerts_log.csv with columns date, time, location, event_type, severity, status.
    """

    def __init__(self, log_file=LOG_FILE_PATH):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
        self.pending = []
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                csv.writer(f).writerow(
                    ["date", "time", "location", "event_type", "severity", "status"]
                )

    def log_event(self, date_str, time_str, location, event_type, severity="High", status="Unreviewed"):
        self.pending.append([date_str, time_str, location, event_type, severity, status])
        try:
            self._ensure_file()
            with open(self.log_file, mode='a', newline='') as f:
                csv.writer(f).writerows(self.pending)
            print(f"[LOGGER] Saved {len(self.pending)} event(s): {severity} alert at {location} ({time_str})")
            self.pending.clear()
        except OSError:
            print(f"[LOGGER] Could not save - {len(self.pending)} event(s) waiting, will retry on next alert.")

    def log_alert(self, alert):
        """
        Convenience method: takes an alert dict exactly as produced by
        backend.alerts.generate_alert() and logs it directly.
        """
        self.log_event(
            alert["date"],
            alert["time"],
            alert["location"],
            alert["event_type"],
            alert["severity"],
            alert["status"],
        )

    def read_recent(self, n=5):
        try:
            with open(self.log_file, newline='') as f:
                return list(csv.DictReader(f))[-n:][::-1]
        except OSError:
            return []