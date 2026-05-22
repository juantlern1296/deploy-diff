"""Parse Docker image layer metadata from manifest and config JSON blobs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LayerInfo:
    """Represents a single Docker image layer."""

    digest: str
    created_by: str = ""
    size: int = 0
    empty: bool = False
    tags: list[str] = field(default_factory=list)

    @property
    def short_digest(self) -> str:
        """Return a shortened digest for display purposes."""
        if self.digest.startswith("sha256:"):
            return self.digest[7:19]
        return self.digest[:12]

    def __str__(self) -> str:
        return f"Layer({self.short_digest}, size={self.size}, cmd={self.created_by[:60]!r})"


def parse_image_config(config_json: str | dict[str, Any]) -> list[LayerInfo]:
    """Extract layer information from a Docker image config JSON.

    Args:
        config_json: Raw JSON string or already-parsed dict of the image config.

    Returns:
        Ordered list of LayerInfo objects, one per non-empty history entry
        that corresponds to a real filesystem layer.
    """
    if isinstance(config_json, str):
        config: dict[str, Any] = json.loads(config_json)
    else:
        config = config_json

    history: list[dict[str, Any]] = config.get("history", [])
    diff_ids: list[str] = config.get("rootfs", {}).get("diff_ids", [])

    layers: list[LayerInfo] = []
    diff_index = 0

    for entry in history:
        is_empty = entry.get("empty_layer", False)
        created_by = entry.get("created_by", "")

        if is_empty:
            layers.append(
                LayerInfo(
                    digest="<empty>",
                    created_by=created_by,
                    empty=True,
                )
            )
        else:
            digest = diff_ids[diff_index] if diff_index < len(diff_ids) else "<unknown>"
            layers.append(
                LayerInfo(
                    digest=digest,
                    created_by=created_by,
                    empty=False,
                )
            )
            diff_index += 1

    return layers
