"""Tracks changes to Docker image ENTRYPOINT and CMD directives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from deploy_diff.diff_engine import LayerChange, ChangeKind


@dataclass
class EntrypointDelta:
    old: Optional[List[str]]
    new: Optional[List[str]]

    def __str__(self) -> str:
        if self.old is None:
            return f"+ {self.new}"
        if self.new is None:
            return f"- {self.old}"
        return f"  {self.old} -> {self.new}"

    def is_added(self) -> bool:
        return self.old is None and self.new is not None

    def is_removed(self) -> bool:
        return self.old is not None and self.new is None

    def is_modified(self) -> bool:
        return self.old is not None and self.new is not None and self.old != self.new


@dataclass
class EntrypointReport:
    entrypoint: Optional[EntrypointDelta]
    cmd: Optional[EntrypointDelta]

    @property
    def has_changes(self) -> bool:
        return self.entrypoint is not None or self.cmd is not None

    def summary(self) -> str:
        parts = []
        if self.entrypoint is not None:
            parts.append(f"ENTRYPOINT: {self.entrypoint}")
        if self.cmd is not None:
            parts.append(f"CMD: {self.cmd}")
        return "\n".join(parts) if parts else "No entrypoint/cmd changes."


def _parse_cmd(raw: object) -> Optional[List[str]]:
    """Normalise CMD/ENTRYPOINT values from image config."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return [str(v) for v in raw] if raw else None
    if isinstance(raw, str):
        return [raw] if raw else None
    return None


def build_entrypoint_report(
    old_config: dict,
    new_config: dict,
) -> EntrypointReport:
    """Compare ENTRYPOINT and CMD fields from two image config dicts."""
    old_ep = _parse_cmd(old_config.get("Entrypoint"))
    new_ep = _parse_cmd(new_config.get("Entrypoint"))
    old_cmd = _parse_cmd(old_config.get("Cmd"))
    new_cmd = _parse_cmd(new_config.get("Cmd"))

    ep_delta: Optional[EntrypointDelta] = None
    if old_ep != new_ep:
        ep_delta = EntrypointDelta(old=old_ep, new=new_ep)

    cmd_delta: Optional[EntrypointDelta] = None
    if old_cmd != new_cmd:
        cmd_delta = EntrypointDelta(old=old_cmd, new=new_cmd)

    return EntrypointReport(entrypoint=ep_delta, cmd=cmd_delta)
