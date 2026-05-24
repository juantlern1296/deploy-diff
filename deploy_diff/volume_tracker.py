"""Tracks changes to Docker volume mount points between two image configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class VolumeDelta:
    path: str
    old: Optional[str]
    new: Optional[str]

    def __str__(self) -> str:
        if self.old is None:
            return f"+ {self.path}"
        if self.new is None:
            return f"- {self.path}"
        return f"~ {self.path}  ({self.old!r} -> {self.new!r})"

    def is_added(self) -> bool:
        return self.old is None and self.new is not None

    def is_removed(self) -> bool:
        return self.old is not None and self.new is None

    def is_modified(self) -> bool:
        return self.old is not None and self.new is not None and self.old != self.new


@dataclass
class VolumeReport:
    deltas: List[VolumeDelta]

    @property
    def total(self) -> int:
        return len(self.deltas)

    @property
    def added(self) -> List[VolumeDelta]:
        return [d for d in self.deltas if d.is_added()]

    @property
    def removed(self) -> List[VolumeDelta]:
        return [d for d in self.deltas if d.is_removed()]

    @property
    def modified(self) -> List[VolumeDelta]:
        return [d for d in self.deltas if d.is_modified()]

    def is_empty(self) -> bool:
        return self.total == 0

    def summary(self) -> str:
        """Return a short human-readable summary of the volume changes."""
        if self.is_empty():
            return "No volume changes."
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.modified:
            parts.append(f"{len(self.modified)} modified")
        return "Volume changes: " + ", ".join(parts) + "."


def _parse_volumes(raw: object) -> Set[str]:
    """Normalise the Volumes field from an image config (dict or None)."""
    if isinstance(raw, dict):
        return set(raw.keys())
    return set()


def diff_volumes(old_config: dict, new_config: dict) -> VolumeReport:
    """Return a VolumeReport describing volume changes between two configs."""
    old_vols = _parse_volumes(old_config.get("Volumes"))
    new_vols = _parse_volumes(new_config.get("Volumes"))

    deltas: List[VolumeDelta] = []

    for path in sorted(old_vols | new_vols):
        if path in old_vols and path not in new_vols:
            deltas.append(VolumeDelta(path=path, old=path, new=None))
        elif path not in old_vols and path in new_vols:
            deltas.append(VolumeDelta(path=path, old=None, new=path))
        # volumes are keyed by path only; no value to compare, so no "modified" case

    return VolumeReport(deltas=deltas)
