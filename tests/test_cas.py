import json
import pytest
from src.graphone.acquisition.fetcher import fetch_url
from pathlib import Path
from src.graphone.acquisition.cas import (
    store_bytes,
    store_snapshot,
    load_manifest,
    verify_manifest
)


def test_store_bytes():
    data = b"hello graphone"

    sha256 = store_bytes(data)

    assert len(sha256) == 64
    assert (f"data/cas/objects/{sha256}").endswith(sha256)

def test_store_snapshot():
    content = b"<html>Hello Graphone</html>"

    snapshot = store_snapshot(
        content,
        "https://example.com",
    )

    assert len(snapshot.sha256) == 64
    assert snapshot.object_path.exists()
    assert snapshot.manifest_path.exists()
    assert snapshot.size_bytes == len(content)

    manifest = json.loads(
    snapshot.manifest_path.read_text(encoding="utf-8")
)

    assert manifest["sha256"] == snapshot.sha256
    assert manifest["source_url"] == "https://example.com"
    assert manifest["content_type"] == "text/html"
    assert manifest["size_bytes"] == len(content)


def test_store_snapshot_manifest():
    content = b"<html>Hello Graphone</html>"

    snapshot = store_snapshot(
        content,
        "https://example.com",
    )

    manifest = json.loads(snapshot.manifest_path.read_text())

    assert manifest["sha256"] == snapshot.sha256
    assert manifest["source_url"] == "https://example.com"
    assert manifest["content_type"] == "text/html"
    assert manifest["size_bytes"] == len(content)

def test_load_manifest():
    content = b"<html>Hello Graphone</html>"

    snapshot = store_snapshot(
        content,
        "https://example.com",
    )

    manifest = load_manifest(snapshot.sha256)

    assert manifest["sha256"] == snapshot.sha256
    assert manifest["source_url"] == "https://example.com"
    assert manifest["size_bytes"] == len(content)

def test_verify_manifest():
    content = b"GraphOne integrity test"

    snapshot = store_snapshot(
        content,
        "https://example.com",
    )

    assert verify_manifest(snapshot.sha256) is True

def test_store_bytes_is_idempotent():
    data = b"same content"

    first_hash = store_bytes(data)
    second_hash = store_bytes(data)

    assert first_hash == second_hash

    object_path = f"data/cas/objects/{first_hash}"

    assert Path(object_path).exists()

@pytest.mark.asyncio
async def test_fetch_url():
    content, final_url, status_code = await fetch_url(
        "https://example.com"
    )

    assert status_code == 200
    assert final_url == "https://example.com"
    assert len(content) > 0