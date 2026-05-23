"""Baseline management: pin a known-good image state for future comparisons."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from deploy_diff.snapshot import Snapshot

DEFAULT_BASELINE_DIR = Path(os.environ.get("DEPLOY_DIFF_BASELINE_DIR", ".deploy_diff/baselines"))


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


@dataclass
class Baseline:
    name: str
    reference: str
    image_id: str
    layers: list[str]

    def to_snapshot(self) -> Snapshot:
        return Snapshot(
            reference=self.reference,
            image_id=self.image_id,
            layers=self.layers,
        )


def _baseline_path(name: str, base_dir: Path = DEFAULT_BASELINE_DIR) -> Path:
    safe = name.replace("/", "_").replace(":", "_")
    return base_dir / f"{safe}.json"


def save_baseline(name: str, snapshot: Snapshot, base_dir: Path = DEFAULT_BASELINE_DIR) -> Path:
    """Persist a named baseline derived from *snapshot*."""
    base_dir.mkdir(parents=True, exist_ok=True)
    path = _baseline_path(name, base_dir)
    payload = {
        "name": name,
        "reference": snapshot.reference,
        "image_id": snapshot.image_id,
        "layers": snapshot.layers,
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_baseline(name: str, base_dir: Path = DEFAULT_BASELINE_DIR) -> Baseline:
    """Load a previously saved baseline by *name*."""
    path = _baseline_path(name, base_dir)
    if not path.exists():
        raise BaselineError(f"No baseline found for '{name}' (looked at {path})")
    data = json.loads(path.read_text())
    return Baseline(**data)


def list_baselines(base_dir: Path = DEFAULT_BASELINE_DIR) -> list[str]:
    """Return the names of all saved baselines."""
    if not base_dir.exists():
        return []
    return [
        p.stem.replace("_", "/", 1)  # best-effort reverse of safe name
        for p in sorted(base_dir.glob("*.json"))
    ]


def delete_baseline(name: str, base_dir: Path = DEFAULT_BASELINE_DIR) -> bool:
    """Remove a baseline file. Returns True if deleted, False if it didn't exist."""
    path = _baseline_path(name, base_dir)
    if path.exists():
        path.unlink()
        return True
    return False
