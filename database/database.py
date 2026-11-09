"""
AIRCTRL Database Connection & Schema Initialization
Manages local SQLite database operations.
"""
import os
import sqlite3
import threading
from utils.logger import get_logger

logger = get_logger("Database")

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airctrl.db")

class Database:
    """Thread-safe SQLite database manager."""
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Activity log
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT NOT NULL,
                        details TEXT,
                        count INTEGER DEFAULT 1
                    )
                """)
                # Quick launch usage
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS quick_launch_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        site_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        url TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Daily aggregated stats
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        date TEXT PRIMARY KEY,
                        clicks INTEGER DEFAULT 0,
                        gestures INTEGER DEFAULT 0,
                        claps INTEGER DEFAULT 0,
                        keystrokes INTEGER DEFAULT 0,
                        websites_opened INTEGER DEFAULT 0,
                        session_seconds INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
            logger.info(f"Database initialized at {DB_FILE}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

db = Database()
