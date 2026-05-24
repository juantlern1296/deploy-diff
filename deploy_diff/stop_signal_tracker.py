"""Tracks changes to the STOPSIGNAL instruction between two image layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from deploy_diff.layer_parser import LayerInfo


@dataclass
class StopSignalDelta:
    old: Optional[str]
    new: Optional[str]

    def __str__(self) -> str:
        if self.is_added:
            return f"stop_signal added: {self.new}"
        if self.is_removed:
            return f"stop_signal removed: {self.old}"
        return f"stop_signal changed: {self.old!r} -> {self.new!r}"

    @property
    def is_added(self) -> bool:
        return self.old is None and self.new is not None

    @property
    def is_removed(self) -> bool:
        return self.old is not None and self.new is None

    @property
    def is_modified(self) -> bool:
        return self.old is not None and self.new is not None and self.old != self.new


@dataclass
class StopSignalReport:
    delta: Optional[StopSignalDelta]

    @property
    def has_changes(self) -> bool:
        return self.delta is not None

    def summary(self) -> str:
        if not self.has_changes:
            return "stop_signal: no changes"
        return str(self.delta)


def _extract_stop_signal(layers: List[LayerInfo]) -> Optional[str]:
    """Return the last non-empty StopSignal value found in the layer list."""
    for layer in reversed(layers):
        raw = (layer.config or {}).get("StopSignal")
        if raw:
            return str(raw).strip()
    return None


def diff_stop_signal(
    old_layers: List[LayerInfo],
    new_layers: List[LayerInfo],
) -> StopSignalReport:
    """Compare the effective STOPSIGNAL between two sets of layers."""
    old_sig = _extract_stop_signal(old_layers)
    new_sig = _extract_stop_signal(new_layers)

    if old_sig == new_sig:
        return StopSignalReport(delta=None)

    return StopSignalReport(delta=StopSignalDelta(old=old_sig, new=new_sig))
