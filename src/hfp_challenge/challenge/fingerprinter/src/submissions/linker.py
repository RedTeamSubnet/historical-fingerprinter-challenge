import hashlib
import json
import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


def generate_fingerprint(payload: dict[str, Any]) -> str:
    normalized = {}
    for key, value in payload.items():
        if value is None:
            normalized[key] = ""
        elif isinstance(value, bool):
            normalized[key] = "1" if value else "0"
        elif isinstance(value, (int, float)):
            normalized[key] = str(value)
        else:
            normalized[key] = str(value).lower().strip()

    sorted_json = json.dumps(normalized, sort_keys=True)
    fingerprint = hashlib.sha256(sorted_json.encode()).hexdigest()

    logger.info(f"Generated fingerprint: {fingerprint[:16]}...")
    return fingerprint


def generate_and_link(payload: dict[str, Any], db_conn: sqlite3.Connection) -> dict[str, Any]:
    fingerprint = generate_fingerprint(payload)

    cursor = db_conn.cursor()

    cursor.execute("""
        SELECT id, fingerprint, created_at, last_seen 
        FROM fingerprints 
        WHERE fingerprint = ?
    """, (fingerprint,))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE fingerprints 
            SET last_seen = CURRENT_TIMESTAMP 
            WHERE fingerprint = ?
        """, (fingerprint,))
        db_conn.commit()
        logger.info(f"Updated existing fingerprint: {fingerprint[:16]}...")
        return {
            "fingerprint": fingerprint,
            "is_new": False,
            "id": existing["id"],
            "created_at": existing["created_at"]
        }
    else:
        cursor.execute("""
            INSERT INTO fingerprints (
                fingerprint, user_agent, ip_address, 
                canvas_geometry, canvas_text, audio_hash,
                color_depth, color_gamut, fonts, os, 
                browser_name, browser_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fingerprint,
            payload.get("user_agent"),
            payload.get("ip_address"),
            payload.get("canvas_geometry"),
            payload.get("canvas_text"),
            payload.get("audio_hash"),
            payload.get("color_depth"),
            payload.get("color_gamut"),
            payload.get("fonts"),
            payload.get("os"),
            payload.get("browser_name"),
            payload.get("browser_version")
        ))
        db_conn.commit()
        logger.info(f"Inserted new fingerprint: {fingerprint[:16]}...")
        return {
            "fingerprint": fingerprint,
            "is_new": True,
            "id": cursor.lastrowid
        }


__all__ = ["generate_fingerprint", "generate_and_link"]
