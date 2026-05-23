"""CLI sub-commands for the audit log (list, clear)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from deploy_diff.audit import AuditEntry, AuditError, DEFAULT_AUDIT_DIR, load_entries


def _build_list_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = sub.add_parser("audit-list", help="List past diff runs from the audit log")
    p.add_argument(
        "--audit-dir",
        metavar="DIR",
        help="Directory containing audit log files (default: ~/.deploy_diff/audit)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Maximum number of entries to show (default: 20)",
    )
    p.set_defaults(func=cmd_audit_list)


def _build_clear_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = sub.add_parser("audit-clear", help="Delete all audit log files")
    p.add_argument(
        "--audit-dir",
        metavar="DIR",
        help="Directory containing audit log files",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    p.set_defaults(func=cmd_audit_clear)


def build_audit_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    _build_list_parser(sub)
    _build_clear_parser(sub)


def _format_entry(e: AuditEntry) -> str:
    tags = f" [{', '.join(e.tags)}]" if e.tags else ""
    return (
        f"{e.timestamp}  {e.reference_a} -> {e.reference_b}  "
        f"+{e.added}/-{e.removed}/~{e.modified}  fmt={e.output_format}{tags}"
    )


def cmd_audit_list(args: argparse.Namespace) -> int:
    audit_dir = Path(args.audit_dir) if getattr(args, "audit_dir", None) else None
    try:
        entries = load_entries(audit_dir)
    except AuditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    recent = entries[-args.limit :]
    if not recent:
        print("No audit entries found.")
        return 0

    for entry in recent:
        print(_format_entry(entry))
    return 0


def cmd_audit_clear(args: argparse.Namespace) -> int:
    audit_dir = Path(args.audit_dir) if getattr(args, "audit_dir", None) else DEFAULT_AUDIT_DIR
    if not args.yes:
        answer = input(f"Delete all audit logs in {audit_dir}? [y/N] ")
        if answer.strip().lower() != "y":
            print("Aborted.")
            return 0
    removed = 0
    for log_file in audit_dir.glob("audit_*.jsonl"):
        log_file.unlink()
        removed += 1
    print(f"Removed {removed} audit log file(s).")
    return 0
