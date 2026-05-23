"""Tracks and compares package-level dependencies extracted from layer changes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from deploy_diff.diff_engine import ChangeKind, LayerChange

# Matches lines like: /usr/lib/python3/dist-packages/requests-2.28.0.dist-info/METADATA
_PKG_RE = re.compile(
    r"/(?:usr/lib/python[\d.]+/dist-packages|usr/local/lib/python[\d.]+/dist-packages|node_modules)/"
    r"([A-Za-z0-9_\-\.]+?)[-_]([\d][\d.a-zA-Z]*)(?:\.dist-info|/package\.json)?"
)


@dataclass
class PackageDelta:
    name: str
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    kind: ChangeKind = ChangeKind.ADDED

    def __str__(self) -> str:
        if self.kind == ChangeKind.ADDED:
            return f"+ {self.name} {self.new_version}"
        if self.kind == ChangeKind.REMOVED:
            return f"- {self.name} {self.old_version}"
        return f"~ {self.name} {self.old_version} -> {self.new_version}"


@dataclass
class DependencyReport:
    added: List[PackageDelta] = field(default_factory=list)
    removed: List[PackageDelta] = field(default_factory=list)
    upgraded: List[PackageDelta] = field(default_factory=list)
    downgraded: List[PackageDelta] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.added) + len(self.removed) + len(self.upgraded) + len(self.downgraded)

    def all_deltas(self) -> List[PackageDelta]:
        return self.added + self.removed + self.upgraded + self.downgraded


def _extract_packages(changes: List[LayerChange]) -> Dict[str, Dict[str, str]]:
    """Return {kind_label: {pkg_name: version}} from a list of layer changes."""
    buckets: Dict[str, Dict[str, str]] = {"added": {}, "removed": {}}
    for change in changes:
        label = "added" if change.kind == ChangeKind.ADDED else "removed" if change.kind == ChangeKind.REMOVED else None
        if label is None:
            continue
        m = _PKG_RE.search(change.path)
        if m:
            buckets[label][m.group(1).lower()] = m.group(2)
    return buckets


def track_dependencies(changes: List[LayerChange]) -> DependencyReport:
    """Analyse layer changes and produce a DependencyReport."""
    buckets = _extract_packages(changes)
    added_pkgs = buckets["added"]
    removed_pkgs = buckets["removed"]

    report = DependencyReport()
    all_names = set(added_pkgs) | set(removed_pkgs)

    for name in sorted(all_names):
        in_added = name in added_pkgs
        in_removed = name in removed_pkgs
        if in_added and in_removed:
            old_v, new_v = removed_pkgs[name], added_pkgs[name]
            kind = ChangeKind.MODIFIED
            delta = PackageDelta(name=name, old_version=old_v, new_version=new_v, kind=kind)
            if old_v < new_v:
                report.upgraded.append(delta)
            else:
                report.downgraded.append(delta)
        elif in_added:
            report.added.append(PackageDelta(name=name, new_version=added_pkgs[name], kind=ChangeKind.ADDED))
        else:
            report.removed.append(PackageDelta(name=name, old_version=removed_pkgs[name], kind=ChangeKind.REMOVED))

    return report
