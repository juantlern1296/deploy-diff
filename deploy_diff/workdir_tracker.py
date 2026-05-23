"""Tracks changes to the WORKDIR instruction between two Docker image configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from deploy_diff.layer_parser import LayerInfo


@dataclass
class WorkdirDelta:
    old: Optional[str]
    new: Optional[str]

    def __str__(self) -> str:
        if self.is_added:
            return f"+ WORKDIR {self.new}"
        if self.is_removed:
            return f"- WORKDIR {self.old}"
        return f"~ WORKDIR {self.old} -> {self.new}"

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
class WorkdirReport:
    delta: Optional[WorkdirDelta]

    @property
    def has_change(self) -> bool:
        return self.delta is not None

    def summary(self) -> str:
        if self.delta is None:
            return "WORKDIR unchanged"
        return str(self.delta)


def _extract_workdir(layers: List[LayerInfo]) -> Optional[str]:
    """Return the last non-empty working directory found in layer commands."""
    workdir: Optional[str] = None
    for layer in layers:
        cmd = layer.command or ""
        upper = cmd.strip().upper()
        if upper.startswith("WORKDIR "):
            workdir = cmd.strip()[len("WORKDIR "):].strip()
    return workdir


def build_workdir_report(
    old_layers: List[LayerInfo],
    new_layers: List[LayerInfo],
) -> WorkdirReport:
    """Compare working directories across two sets of layers."""
    old_wd = _extract_workdir(old_layers)
    new_wd = _extract_workdir(new_layers)

    if old_wd == new_wd:
        return WorkdirReport(delta=None)

    return WorkdirReport(delta=WorkdirDelta(old=old_wd, new=new_wd))
