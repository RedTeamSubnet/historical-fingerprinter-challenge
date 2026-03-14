import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "database.db"


def initialize_db(db_path: str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = str(DB_PATH)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT UNIQUE NOT NULL,
            visitor_id TEXT,
            user_agent TEXT,
            ip_address TEXT,
            canvas_geometry TEXT,
            canvas_text TEXT,
            audio_hash TEXT,
            color_depth INTEGER,
            color_gamut TEXT,
            fonts TEXT,
            os TEXT,
            browser_name TEXT,
            browser_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    logger.info(f"Database initialized at {db_path}")

    return conn


__all__ = ["initialize_db"]
