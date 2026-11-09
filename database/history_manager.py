"""
AIRCTRL History & Analytics Manager
Provides high-level APIs for tracking, querying, and aggregating usage data.
"""
import datetime
from typing import Dict, List, Any, Optional
from database.database import db
from utils.logger import get_logger

logger = get_logger("HistoryManager")

class HistoryManager:
    def __init__(self):
        self._db = db

    def _today_str(self) -> str:
        return datetime.date.today().isoformat()

    def record_event(self, event_type: str, details: str = "", count: int = 1):
        """Records an interaction event (click, gesture, clap, key, website)."""
        today = self._today_str()
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO activity_log (event_type, details, count) VALUES (?, ?, ?)",
                    (event_type, details, count)
                )

                # Update daily stats
                col_map = {
                    "click": "clicks",
                    "gesture": "gestures",
                    "clap": "claps",
                    "key": "keystrokes",
                    "website": "websites_opened"
                }
                col = col_map.get(event_type)
                if col:
                    cursor.execute(f"""
                        INSERT INTO daily_stats (date, {col})
                        VALUES (?, ?)
                        ON CONFLICT(date) DO UPDATE SET {col} = {col} + ?
                    """, (today, count, count))

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record event '{event_type}': {e}")

    def record_website_open(self, site_id: str, title: str, url: str):
        """Records a quick launch website opening."""
        self.record_event("website", f"{title} ({url})", 1)
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO quick_launch_log (site_id, title, url) VALUES (?, ?, ?)",
                    (site_id, title, url)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record quick launch for '{title}': {e}")

    def update_session_time(self, seconds: int):
        """Updates cumulative session active seconds for today."""
        today = self._today_str()
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO daily_stats (date, session_seconds)
                    VALUES (?, ?)
                    ON CONFLICT(date) DO UPDATE SET session_seconds = session_seconds + ?
                """, (today, seconds, seconds))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update session time: {e}")

    def get_totals(self) -> Dict[str, int]:
        """Returns total lifetime interactions across all categories."""
        res = {
            "clicks": 0,
            "gestures": 0,
            "claps": 0,
            "keystrokes": 0,
            "websites_opened": 0,
            "session_seconds": 0
        }
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(clicks), 0) as total_clicks,
                        COALESCE(SUM(gestures), 0) as total_gestures,
                        COALESCE(SUM(claps), 0) as total_claps,
                        COALESCE(SUM(keystrokes), 0) as total_keystrokes,
                        COALESCE(SUM(websites_opened), 0) as total_websites,
                        COALESCE(SUM(session_seconds), 0) as total_seconds
                    FROM daily_stats
                """)
                row = cursor.fetchone()
                if row:
                    res["clicks"] = row["total_clicks"]
                    res["gestures"] = row["total_gestures"]
                    res["claps"] = row["total_claps"]
                    res["keystrokes"] = row["total_keystrokes"]
                    res["websites_opened"] = row["total_websites"]
                    res["session_seconds"] = row["total_seconds"]
        except Exception as e:
            logger.error(f"Failed to fetch totals: {e}")
        return res

    def get_recent_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent activity log entries."""
        activities = []
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT timestamp, event_type, details, count FROM activity_log ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                for row in cursor.fetchall():
                    activities.append({
                        "timestamp": row["timestamp"],
                        "event_type": row["event_type"],
                        "details": row["details"],
                        "count": row["count"]
                    })
        except Exception as e:
            logger.error(f"Failed to fetch recent activities: {e}")
        return activities

    def get_daily_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Returns daily stats for the last N days."""
        trend = []
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, clicks, gestures, claps, keystrokes, websites_opened, session_seconds
                    FROM daily_stats
                    ORDER BY date DESC LIMIT ?
                """, (days,))
                for row in reversed(cursor.fetchall()):
                    trend.append({
                        "date": row["date"],
                        "clicks": row["clicks"],
                        "gestures": row["gestures"],
                        "claps": row["claps"],
                        "keystrokes": row["keystrokes"],
                        "websites_opened": row["websites_opened"],
                        "session_seconds": row["session_seconds"]
                    })
        except Exception as e:
            logger.error(f"Failed to fetch daily trend: {e}")
        return trend

    def get_most_frequent_website(self) -> Optional[Dict[str, Any]]:
        """Returns the most frequently opened website."""
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, url, COUNT(*) as open_count
                    FROM quick_launch_log
                    GROUP BY title, url
                    ORDER BY open_count DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return {
                        "title": row["title"],
                        "url": row["url"],
                        "open_count": row["open_count"]
                    }
        except Exception as e:
            logger.error(f"Failed to get top website: {e}")
        return None

    def clear_history(self):
        """Clears all logged history and statistics."""
        try:
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM activity_log")
                cursor.execute("DELETE FROM quick_launch_log")
                cursor.execute("DELETE FROM daily_stats")
                conn.commit()
            logger.info("Cleared all activity history.")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")

history = HistoryManager()

