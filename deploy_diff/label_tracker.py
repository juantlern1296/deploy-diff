"""Track changes to Docker image labels between two layer sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelDelta:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]

    def __str__(self) -> str:
        if self.old_value is None:
            return f"+ {self.key}={self.new_value}"
        if self.new_value is None:
            return f"- {self.key}={self.old_value}"
        return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"

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
class LabelReport:
    deltas: List[LabelDelta] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.deltas)

    @property
    def added(self) -> List[LabelDelta]:
        return [d for d in self.deltas if d.is_added]

    @property
    def removed(self) -> List[LabelDelta]:
        return [d for d in self.deltas if d.is_removed]

    @property
    def modified(self) -> List[LabelDelta]:
        return [d for d in self.deltas if d.is_modified]

    def is_empty(self) -> bool:
        return self.total == 0


def diff_labels(
    old: Dict[str, str],
    new: Dict[str, str],
) -> LabelReport:
    """Compute label deltas between two label dicts."""
    deltas: List[LabelDelta] = []

    all_keys = set(old) | set(new)
    for key in sorted(all_keys):
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val == new_val:
            continue
        deltas.append(LabelDelta(key=key, old_value=old_val, new_value=new_val))

    return LabelReport(deltas=deltas)
