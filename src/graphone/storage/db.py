import sqlite3
from pathlib import Path


DB_PATH = Path("data/graphone.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS acquisitions (
                sha256 TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

def record_acquisition(
    sha256: str,
    source_url: str,
    created_at: str,
) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO acquisitions
            (sha256, source_url, created_at)
            VALUES (?, ?, ?)
            """,
            (sha256, source_url, created_at),
        )

    return cursor.rowcount == 1

def acquisition_exists(sha256: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM acquisitions
            WHERE sha256 = ?
            """,
            (sha256,),
        ).fetchone()

    return row is not None