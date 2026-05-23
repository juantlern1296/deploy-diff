"""Audit log — records every diff run with metadata for traceability."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_DIR = Path.home() / ".deploy_diff" / "audit"


@dataclass
class AuditEntry:
    timestamp: str
    reference_a: str
    reference_b: str
    added: int
    removed: int
    modified: int
    output_format: str
    output_path: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class AuditError(Exception):
    """Raised when an audit operation fails."""


def _audit_path(audit_dir: Path) -> Path:
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return audit_dir / f"audit_{stamp}.jsonl"


def record(entry: AuditEntry, audit_dir: Optional[Path] = None) -> Path:
    """Append *entry* to today's audit log. Returns the log file path."""
    target = _audit_path(audit_dir or DEFAULT_AUDIT_DIR)
    try:
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
    except OSError as exc:
        raise AuditError(f"Failed to write audit log: {exc}") from exc
    return target


def load_entries(audit_dir: Optional[Path] = None) -> List[AuditEntry]:
    """Return all audit entries found in *audit_dir* (all daily files)."""
    base = audit_dir or DEFAULT_AUDIT_DIR
    entries: List[AuditEntry] = []
    if not base.exists():
        return entries
    for log_file in sorted(base.glob("audit_*.jsonl")):
        with log_file.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(AuditEntry(**data))
    return entries


def make_entry(
    reference_a: str,
    reference_b: str,
    added: int,
    removed: int,
    modified: int,
    output_format: str = "text",
    output_path: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> AuditEntry:
    return AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        reference_a=reference_a,
        reference_b=reference_b,
        added=added,
        removed=removed,
        modified=modified,
        output_format=output_format,
        output_path=output_path,
        tags=tags or [],
    )
