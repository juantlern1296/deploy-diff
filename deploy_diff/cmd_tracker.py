"""Track changes to the CMD instruction between two image layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from deploy_diff.layer_parser import LayerInfo


@dataclass
class CmdDelta:
    old: Optional[List[str]]
    new: Optional[List[str]]

    def __str__(self) -> str:
        if self.is_added:
            return f"CMD added: {self.new}"
        if self.is_removed:
            return f"CMD removed (was {self.old})"
        return f"CMD changed: {self.old!r} -> {self.new!r}"

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
class CmdReport:
    delta: Optional[CmdDelta]

    @property
    def has_changes(self) -> bool:
        return self.delta is not None

    def summary(self) -> str:
        if not self.has_changes:
            return "CMD: no changes"
        return f"CMD: {self.delta}"


def _extract_cmd(layer: LayerInfo) -> Optional[List[str]]:
    raw = layer.extra.get("Cmd") if layer.extra else None
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    return [str(raw)]


def diff_cmd(old: LayerInfo, new: LayerInfo) -> CmdReport:
    """Compare CMD values from two LayerInfo objects."""
    old_cmd = _extract_cmd(old)
    new_cmd = _extract_cmd(new)

    if old_cmd == new_cmd:
        return CmdReport(delta=None)

    return CmdReport(delta=CmdDelta(old=old_cmd, new=new_cmd))
