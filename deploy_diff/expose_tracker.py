"""Tracks changes to exposed ports/protocols declared via EXPOSE in image configs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from deploy_diff.layer_parser import LayerInfo


@dataclass
class ExposeDelta:
    key: str  # e.g. "80/tcp"
    old_value: Optional[str]
    new_value: Optional[str]

    def __str__(self) -> str:
        if self.old_value is None:
            return f"+ {self.key}"
        if self.new_value is None:
            return f"- {self.key}"
        return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"

    def is_added(self) -> bool:
        return self.old_value is None and self.new_value is not None

    def is_removed(self) -> bool:
        return self.old_value is not None and self.new_value is None

    def is_modified(self) -> bool:
        return self.old_value is not None and self.new_value is not None


@dataclass
class ExposeReport:
    deltas: List[ExposeDelta]

    @property
    def total(self) -> int:
        return len(self.deltas)

    @property
    def added(self) -> List[ExposeDelta]:
        return [d for d in self.deltas if d.is_added()]

    @property
    def removed(self) -> List[ExposeDelta]:
        return [d for d in self.deltas if d.is_removed()]

    @property
    def modified(self) -> List[ExposeDelta]:
        return [d for d in self.deltas if d.is_modified()]

    def is_empty(self) -> bool:
        return self.total == 0


def _parse_exposed_ports(layer: Optional[LayerInfo]) -> dict:
    """Return a dict of port/proto -> '' from a layer's exposed_ports field."""
    if layer is None:
        return {}
    raw = getattr(layer, "exposed_ports", None) or {}
    if isinstance(raw, dict):
        return {k: "" for k in raw}
    if isinstance(raw, (list, tuple)):
        return {str(p): "" for p in raw}
    return {}


def diff_exposed_ports(
    old: Optional[LayerInfo],
    new: Optional[LayerInfo],
) -> ExposeReport:
    """Compare exposed ports between two layers and return an ExposeReport."""
    old_ports = _parse_exposed_ports(old)
    new_ports = _parse_exposed_ports(new)

    all_keys = sorted(set(old_ports) | set(new_ports))
    deltas: List[ExposeDelta] = []

    for key in all_keys:
        o = old_ports.get(key)
        n = new_ports.get(key)
        if key not in old_ports:
            deltas.append(ExposeDelta(key=key, old_value=None, new_value=n if n is not None else ""))
        elif key not in new_ports:
            deltas.append(ExposeDelta(key=key, old_value=o if o is not None else "", new_value=None))
        elif o != n:
            deltas.append(ExposeDelta(key=key, old_value=o, new_value=n))

    return ExposeReport(deltas=deltas)
