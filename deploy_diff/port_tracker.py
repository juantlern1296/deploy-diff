"""Track exposed port changes between two image layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PortDelta:
    port: str
    old_value: Optional[str]
    new_value: Optional[str]

    def __str__(self) -> str:
        if self.old_value is None:
            return f"+ {self.port}"
        if self.new_value is None:
            return f"- {self.port}"
        return f"~ {self.port} ({self.old_value} -> {self.new_value})"

    @property
    def is_added(self) -> bool:
        return self.old_value is None and self.new_value is not None

    @property
    def is_removed(self) -> bool:
        return self.old_value is not None and self.new_value is None

    @property
    def is_modified(self) -> bool:
        return self.old_value is not None and self.new_value is not None


@dataclass
class PortReport:
    deltas: List[PortDelta] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.deltas)

    @property
    def added(self) -> List[PortDelta]:
        return [d for d in self.deltas if d.is_added]

    @property
    def removed(self) -> List[PortDelta]:
        return [d for d in self.deltas if d.is_removed]

    @property
    def modified(self) -> List[PortDelta]:
        return [d for d in self.deltas if d.is_modified]

    def has_changes(self) -> bool:
        return self.total > 0


def _parse_ports(raw: dict) -> dict:
    """Normalise the ExposedPorts dict from an image config."""
    if not isinstance(raw, dict):
        return {}
    return {k: k for k in raw.keys()}


def build_port_report(old_config: dict, new_config: dict) -> PortReport:
    """Compare ExposedPorts sections of two image configs."""
    old_ports = _parse_ports(old_config.get("ExposedPorts", {}))
    new_ports = _parse_ports(new_config.get("ExposedPorts", {}))

    all_keys = set(old_ports) | set(new_ports)
    deltas: List[PortDelta] = []

    for port in sorted(all_keys):
        old_val = old_ports.get(port)
        new_val = new_ports.get(port)
        if old_val != new_val:
            deltas.append(PortDelta(port=port, old_value=old_val, new_value=new_val))

    return PortReport(deltas=deltas)
