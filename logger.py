import csv
import os

import pandas as pd

from config import LOG_FILE_PATH


class EventLogger:
    """
    Writes alert events to a CSV log.
    Column names and default path are matched to what app.py expects:
    logs/alerts_log.csv with columns:
        date, time, location, event_type, severity, status, snapshot
    """

    COLUMNS = ["date", "time", "location", "event_type", "severity", "status", "snapshot"]

    def __init__(self, log_file=LOG_FILE_PATH):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
        self.pending = []
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode="w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(self.COLUMNS)
        else:
            try:
                with open(self.log_file, mode="r", newline="", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                if first_line and first_line != ",".join(self.COLUMNS):
                    with open(self.log_file, mode="r", newline="", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        rows = []
                        for r in reader:
                            if not r or not any(r):
                                continue
                            while len(r) < len(self.COLUMNS):
                                r.append("")
                            rows.append(r[:len(self.COLUMNS)])
                    with open(self.log_file, mode="w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(self.COLUMNS)
                        writer.writerows(rows)
            except Exception as e:
                print(f"[LOGGER] Header check note: {e}")

    def log_event(
        self,
        date_str,
        time_str,
        location,
        event_type,
        severity="High",
        status="Unreviewed",
        snapshot="",
    ):
        self.pending.append(
            [date_str, time_str, location, event_type, severity, status, snapshot]
        )
        try:
            self._ensure_file()
            with open(self.log_file, mode="a", newline="") as f:
                csv.writer(f).writerows(self.pending)
            print(
                f"[LOGGER] Saved {len(self.pending)} event(s): "
                f"{severity} alert at {location} ({time_str})"
            )
            self.pending.clear()
        except OSError:
            print(
                f"[LOGGER] Could not save — {len(self.pending)} event(s) "
                "pending, will retry on next alert."
            )

    def log_alert(self, alert, snapshot_path=""):
        """
        Convenience method: takes an alert dict exactly as produced by
        backend.alerts.generate_alert() and logs it directly.
        Optionally attaches a path to a saved snapshot image.
        """
        self.log_event(
            alert["date"],
            alert["time"],
            alert["location"],
            alert["event_type"],
            alert["severity"],
            alert["status"],
            snapshot_path,
        )

    def update_status(self, row_index, new_status):
        """
        Persists a status change for a logged alert back to the CSV file.

        Parameters
        ----------
        row_index : int
            0-based row index in the CSV data (matches the DataFrame index
            returned by load_alerts_from_log before the 'id' column is added).
        new_status : str
            One of 'Unreviewed', 'Under Review', 'Resolved'.

        Returns
        -------
        bool  — True on success, False if the write failed.
        """
        try:
            df = pd.read_csv(self.log_file, on_bad_lines="skip")
            # Add missing columns for files created before the snapshot field existed
            for col in self.COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            if row_index < 0 or row_index >= len(df):
                print(f"[LOGGER] update_status: index {row_index} out of range.")
                return False
            df.at[row_index, "status"] = new_status
            df.to_csv(self.log_file, index=False, encoding="utf-8")
            print(f"[LOGGER] Row {row_index} status -> '{new_status}'")
            return True
        except Exception as e:
            print(f"[LOGGER] update_status failed: {e}")
            return False

    def read_recent(self, n=5):
        try:
            with open(self.log_file, newline="") as f:
                return list(csv.DictReader(f))[-n:][::-1]
        except OSError:
            return []