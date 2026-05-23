"""Track environment variable changes between two image layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from deploy_diff.diff_engine import ChangeKind, LayerChange


@dataclass
class EnvDelta:
    key: str
    kind: ChangeKind
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        if self.kind == ChangeKind.ADDED:
            return f"+ {self.key}={self.new_value}"
        if self.kind == ChangeKind.REMOVED:
            return f"- {self.key}={self.old_value}"
        return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"


@dataclass
class EnvReport:
    deltas: List[EnvDelta] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.deltas)

    @property
    def added(self) -> List[EnvDelta]:
        return [d for d in self.deltas if d.kind == ChangeKind.ADDED]

    @property
    def removed(self) -> List[EnvDelta]:
        return [d for d in self.deltas if d.kind == ChangeKind.REMOVED]

    @property
    def modified(self) -> List[EnvDelta]:
        return [d for d in self.deltas if d.kind == ChangeKind.MODIFIED]

    def is_empty(self) -> bool:
        return self.total == 0


def _parse_env_list(env_list: List[str]) -> Dict[str, str]:
    """Convert a list of KEY=VALUE strings to a dict."""
    result: Dict[str, str] = {}
    for entry in env_list:
        if "=" in entry:
            key, _, value = entry.partition("=")
            result[key.strip()] = value
        else:
            result[entry.strip()] = ""
    return result


def build_env_report(old_env: List[str], new_env: List[str]) -> EnvReport:
    """Compare two ENV lists and return an EnvReport of differences."""
    old = _parse_env_list(old_env)
    new = _parse_env_list(new_env)

    deltas: List[EnvDelta] = []

    for key in sorted(set(old) | set(new)):
        if key not in old:
            deltas.append(EnvDelta(key, ChangeKind.ADDED, new_value=new[key]))
        elif key not in new:
            deltas.append(EnvDelta(key, ChangeKind.REMOVED, old_value=old[key]))
        elif old[key] != new[key]:
            deltas.append(EnvDelta(key, ChangeKind.MODIFIED, old_value=old[key], new_value=new[key]))

    return EnvReport(deltas=deltas)
