"""Snapshot support — save and load layer snapshots for later comparison."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_SNAPSHOT_DIR = Path.home() / ".deploy_diff" / "snapshots"


@dataclass
class Snapshot:
    reference: str
    image_id: str
    layers: List[dict]
    created_at: str

    @staticmethod
    def from_manifest(manifest) -> "Snapshot":
        """Build a Snapshot from an ImageManifest."""
        return Snapshot(
            reference=manifest.reference,
            image_id=manifest.image_id,
            layers=[{"digest": l.digest, "empty": l.is_empty} for l in manifest.layers],
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class SnapshotError(Exception):
    pass


def _snapshot_path(reference: str, directory: Path) -> Path:
    safe = reference.replace("/", "_").replace(":", "@")
    return directory / f"{safe}.json"


def save_snapshot(snapshot: Snapshot, directory: Optional[Path] = None) -> Path:
    """Persist a snapshot to disk; returns the file path."""
    directory = Path(directory or DEFAULT_SNAPSHOT_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(snapshot.reference, directory)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(snapshot), fh, indent=2)
    return path


def load_snapshot(reference: str, directory: Optional[Path] = None) -> Snapshot:
    """Load a previously saved snapshot; raises SnapshotError if not found."""
    directory = Path(directory or DEFAULT_SNAPSHOT_DIR)
    path = _snapshot_path(reference, directory)
    if not path.exists():
        raise SnapshotError(f"No snapshot found for '{reference}' at {path}")
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SnapshotError(
                f"Snapshot file for '{reference}' is corrupted: {exc}"
            ) from exc
    missing = {f for f in ("reference", "image_id", "layers", "created_at")} - data.keys()
    if missing:
        raise SnapshotError(
            f"Snapshot file for '{reference}' is missing fields: {', '.join(sorted(missing))}"
        )
    return Snapshot(**data)


def list_snapshots(directory: Optional[Path] = None) -> List[str]:
    """Return references of all saved snapshots in the directory."""
    directory = Path(directory or DEFAULT_SNAPSHOT_DIR)
    if not directory.exists():
        return []
    return [
        p.stem.replace("_", "/", 1).replace("@", ":")
        for p in sorted(directory.glob("*.json"))
    ]
