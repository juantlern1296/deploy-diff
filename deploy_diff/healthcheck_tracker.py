"""Track changes to Docker HEALTHCHECK configuration between two image layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class HealthcheckDelta:
    """Represents a change in HEALTHCHECK configuration."""

    old: Optional[dict]
    new: Optional[dict]

    def __str__(self) -> str:  # noqa: D105
        if self.is_added:
            return f"healthcheck added: {_fmt(self.new)}"
        if self.is_removed:
            return f"healthcheck removed: {_fmt(self.old)}"
        return f"healthcheck changed: {_fmt(self.old)} -> {_fmt(self.new)}"

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
class HealthcheckReport:
    """Aggregated healthcheck diff between two images."""

    delta: Optional[HealthcheckDelta]

    @property
    def has_changes(self) -> bool:
        return self.delta is not None

    def summary(self) -> str:
        if not self.has_changes:
            return "No healthcheck changes."
        return str(self.delta)


def _fmt(hc: Optional[dict]) -> str:
    if hc is None:
        return "(none)"
    test = hc.get("Test", [])
    interval = hc.get("Interval", 0)
    retries = hc.get("Retries", 0)
    cmd = " ".join(str(t) for t in test) if test else "(empty)"
    return f"[{cmd}] interval={interval} retries={retries}"


def _extract_healthcheck(layer: dict) -> Optional[dict]:
    config = layer.get("config") or layer.get("Config") or {}
    return config.get("Healthcheck") or config.get("healthcheck")


def diff_healthcheck(old_layer: dict, new_layer: dict) -> HealthcheckReport:
    """Compare HEALTHCHECK configs from two layer config dicts."""
    old_hc = _extract_healthcheck(old_layer)
    new_hc = _extract_healthcheck(new_layer)

    if old_hc == new_hc:
        return HealthcheckReport(delta=None)

    delta = HealthcheckDelta(old=old_hc, new=new_hc)
    return HealthcheckReport(delta=delta)
