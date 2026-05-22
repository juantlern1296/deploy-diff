"""Simple file-based cache for Docker image inspection results."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "deploy-diff"


def _cache_key(reference: str) -> str:
    """Derive a safe filename key from an image reference."""
    digest = hashlib.sha256(reference.encode()).hexdigest()[:16]
    safe = reference.replace("/", "_").replace(":", "@")
    # Trim long names so paths stay reasonable
    safe = safe[:64]
    return f"{safe}-{digest}.json"


def cache_path(reference: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """Return the full path where *reference* would be cached."""
    return cache_dir / _cache_key(reference)


def load(reference: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Optional[Any]:
    """Return cached data for *reference*, or ``None`` if not present."""
    path = cache_path(reference, cache_dir)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def save(reference: str, data: Any, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """Persist *data* for *reference* and return the file path written."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(reference, cache_dir)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return path


def invalidate(reference: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> bool:
    """Delete cached entry for *reference*. Returns True if a file was removed."""
    path = cache_path(reference, cache_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def clear(cache_dir: Path = DEFAULT_CACHE_DIR) -> int:
    """Remove all cached entries. Returns count of files deleted."""
    if not cache_dir.exists():
        return 0
    removed = 0
    for entry in cache_dir.glob("*.json"):
        entry.unlink()
        removed += 1
    return removed
