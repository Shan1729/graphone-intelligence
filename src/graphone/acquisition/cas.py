from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CAS_ROOT = Path("data/cas")
OBJECTS_DIR = CAS_ROOT / "objects"
MANIFESTS_DIR = CAS_ROOT / "manifests"


@dataclass(frozen=True)
class Snapshot:
    sha256: str
    object_path: Path
    manifest_path: Path
    size_bytes: int


def store_snapshot(
    content: bytes,
    source_url: str,
    content_type: str = "text/html",
) -> Snapshot:
    """
    Store raw content using its SHA-256 hash as its immutable identifier.
    """

    sha256 = hashlib.sha256(content).hexdigest()

    object_path = OBJECTS_DIR / sha256
    manifest_path = MANIFESTS_DIR / f"{sha256}.json"

    OBJECTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write raw content only if this snapshot does not already exist.
    if not object_path.exists():
        object_path.write_bytes(content)

    manifest = {
        "sha256": sha256,
        "source_url": source_url,
        "content_type": content_type,
        "size_bytes": len(content),
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }

    # Write provenance metadata only once.
    if not manifest_path.exists():
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

    return Snapshot(
        sha256=sha256,
        object_path=object_path,
        manifest_path=manifest_path,
        size_bytes=len(content),
    )

def store_bytes(data: bytes) -> str:
    sha256 = hashlib.sha256(data).hexdigest()

    object_path = OBJECTS_DIR / sha256

    if not object_path.exists():
        object_path.write_bytes(data)

    return sha256

def load_manifest(sha256: str) -> dict:
    manifest_path = MANIFESTS_DIR / f"{sha256}.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {sha256}")

    return json.loads(manifest_path.read_text(encoding="utf-8"))

def verify_manifest(sha256: str) -> bool:
    manifest = load_manifest(sha256)

    object_path = OBJECTS_DIR / sha256

    if not object_path.exists():
        return False

    data = object_path.read_bytes()
    actual_sha256 = hashlib.sha256(data).hexdigest()

    return actual_sha256 == manifest["sha256"]