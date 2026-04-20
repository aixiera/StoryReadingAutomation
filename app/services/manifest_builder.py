from __future__ import annotations

from pathlib import Path

from app.core.utils import write_json
from app.models.manifest import Manifest


def save_manifest(manifest: Manifest, path: Path) -> Path:
    manifest.manifest_path = str(path.resolve())
    write_json(path, manifest)
    return path

