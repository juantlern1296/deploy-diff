"""Track and compare Docker image tags across references."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class TagTrackerError(Exception):
    """Raised when tag tracking operations fail."""


@dataclass
class TagDelta:
    """Represents a change in image tag between two states."""

    reference: str
    old_tag: Optional[str]
    new_tag: Optional[str]

    def __str__(self) -> str:
        if self.old_tag is None:
            return f"{self.reference}: (none) -> {self.new_tag}"
        if self.new_tag is None:
            return f"{self.reference}: {self.old_tag} -> (removed)"
        return f"{self.reference}: {self.old_tag} -> {self.new_tag}"

    @property
    def is_promotion(self) -> bool:
        """True when the tag change looks like a version bump (e.g. v1 -> v2)."""
        if self.old_tag is None or self.new_tag is None:
            return False
        return self.old_tag != self.new_tag


@dataclass
class TagReport:
    """Aggregated result of comparing two sets of image tags."""

    deltas: List[TagDelta] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.deltas)

    @property
    def promotions(self) -> List[TagDelta]:
        return [d for d in self.deltas if d.is_promotion]

    def summary(self) -> str:
        if not self.deltas:
            return "No tag changes detected."
        lines = [str(d) for d in self.deltas]
        return "\n".join(lines)


def compare_tags(
    before: dict[str, str],
    after: dict[str, str],
) -> TagReport:
    """Compare two {reference: tag} mappings and return a TagReport.

    Args:
        before: Mapping of image reference to tag before deployment.
        after:  Mapping of image reference to tag after deployment.

    Returns:
        TagReport containing all detected deltas.
    """
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise TagTrackerError("Both 'before' and 'after' must be dicts.")

    all_refs = set(before) | set(after)
    deltas: List[TagDelta] = []

    for ref in sorted(all_refs):
        old = before.get(ref)
        new = after.get(ref)
        if old != new:
            deltas.append(TagDelta(reference=ref, old_tag=old, new_tag=new))

    return TagReport(deltas=deltas)
