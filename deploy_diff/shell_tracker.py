"""Track changes to the shell (Cmd) configuration between two image layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .layer_parser import LayerInfo


@dataclass
class ShellDelta:
    old: Optional[List[str]]
    new: Optional[List[str]]

    def __str__(self) -> str:  # noqa: D401
        if self.is_added:
            return f"shell added: {self.new}"
        if self.is_removed:
            return f"shell removed: {self.old}"
        return f"shell changed: {self.old!r} -> {self.new!r}"

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
class ShellReport:
    delta: Optional[ShellDelta]

    @property
    def has_changes(self) -> bool:
        return self.delta is not None

    def summary(self) -> str:
        if not self.has_changes:
            return "shell: no changes"
        return f"shell: {self.delta}"


def _extract_shell(layer: LayerInfo) -> Optional[List[str]]:
    """Return the Shell list from a LayerInfo, or None if absent."""
    raw = (layer.config or {}).get("Shell")
    if not raw:
        return None
    return list(raw)


def diff_shell(old: LayerInfo, new: LayerInfo) -> ShellReport:
    """Compare the Shell config between two layers and return a ShellReport."""
    old_shell = _extract_shell(old)
    new_shell = _extract_shell(new)

    if old_shell == new_shell:
        return ShellReport(delta=None)

    return ShellReport(delta=ShellDelta(old=old_shell, new=new_shell))
