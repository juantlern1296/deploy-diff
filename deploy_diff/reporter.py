"""Generates structured report objects from changelog data."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .diff_engine import ChangeKind, LayerChange
from .formatter import format_changelog


@dataclass
class ReportMeta:
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    base_image: Optional[str] = None
    target_image: Optional[str] = None


@dataclass
class ReportSummary:
    total: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0
    unchanged: int = 0


@dataclass
class Report:
    meta: ReportMeta
    summary: ReportSummary
    changes: List[dict]
    text: str

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            {
                "meta": asdict(self.meta),
                "summary": asdict(self.summary),
                "changes": self.changes,
            },
            indent=indent,
        )


def build_report(
    changes: List[LayerChange],
    base_image: Optional[str] = None,
    target_image: Optional[str] = None,
) -> Report:
    """Build a Report from a list of LayerChange objects."""
    summary = ReportSummary(total=len(changes))
    for c in changes:
        if c.kind == ChangeKind.ADDED:
            summary.added += 1
        elif c.kind == ChangeKind.REMOVED:
            summary.removed += 1
        elif c.kind == ChangeKind.MODIFIED:
            summary.modified += 1
        else:
            summary.unchanged += 1

    change_dicts = [
        {
            "kind": c.kind.value,
            "digest": c.digest,
            "command": c.command,
            "size_bytes": c.size_bytes,
            "empty": c.empty,
        }
        for c in changes
    ]

    return Report(
        meta=ReportMeta(base_image=base_image, target_image=target_image),
        summary=summary,
        changes=change_dicts,
        text=format_changelog(changes),
    )
