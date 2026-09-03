from src.graphone.storage.db import (
    get_connection,
    init_db,
    record_acquisition,
    acquisition_exists,
)

def test_init_db():
    init_db()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='acquisitions'
            """
        ).fetchone()

    assert row is not None

def test_record_acquisition_deduplicates():
    init_db()

    with get_connection() as conn:
        conn.execute(
              "DELETE FROM acquisitions WHERE sha256 = ?",
              ("abc123",),
        )



    first = record_acquisition(
        "abc123",
        "https://example.com",
        "2026-08-30T21:00:00",
    )

    second = record_acquisition(
        "abc123",
        "https://example.com",
        "2026-08-30T21:01:00",
    )

    assert first is True
    assert second is False

def test_acquisition_exists():
    init_db()

    sha256 = "lookup-test-123"

    record_acquisition(
        sha256,
        "https://example.com",
        "2026-08-30T21:00:00",
    )

    assert acquisition_exists(sha256) is True
    assert acquisition_exists("does-not-exist") is False