"""Core diffing engine — compares two lists of LayerInfo objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .layer_parser import LayerInfo


class ChangeKind(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass
class LayerChange:
    """Describes a single layer-level change between two images."""

    kind: ChangeKind
    layer: LayerInfo

    def __str__(self) -> str:
        symbol = {ChangeKind.ADDED: "+", ChangeKind.REMOVED: "-", ChangeKind.UNCHANGED: " "}[
            self.kind
        ]
        return f"{symbol} [{self.layer.short_digest}] {self.layer.created_by[:80]}"


def diff_layers(
    base: Sequence[LayerInfo],
    target: Sequence[LayerInfo],
) -> list[LayerChange]:
    """Produce an ordered list of changes from *base* to *target*.

    Uses digest-based comparison so that reordered-but-identical layers are
    still detected as unchanged.

    Args:
        base:   Layers from the "old" / base image.
        target: Layers from the "new" / target image.

    Returns:
        List of LayerChange entries representing the diff.
    """
    base_digests = {layer.digest: layer for layer in base if not layer.empty}
    target_digests = {layer.digest: layer for layer in target if not layer.empty}

    changes: list[LayerChange] = []

    for layer in base:
        if layer.empty:
            continue
        if layer.digest in target_digests:
            changes.append(LayerChange(kind=ChangeKind.UNCHANGED, layer=layer))
        else:
            changes.append(LayerChange(kind=ChangeKind.REMOVED, layer=layer))

    for layer in target:
        if layer.empty:
            continue
        if layer.digest not in base_digests:
            changes.append(LayerChange(kind=ChangeKind.ADDED, layer=layer))

    return changes


def summary(changes: list[LayerChange]) -> dict[str, int]:
    """Return a quick count of added / removed / unchanged layers."""
    counts: dict[str, int] = {k.value: 0 for k in ChangeKind}
    for change in changes:
        counts[change.kind.value] += 1
    return counts
