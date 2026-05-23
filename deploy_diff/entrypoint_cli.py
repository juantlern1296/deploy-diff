"""CLI sub-command for comparing ENTRYPOINT / CMD between two image configs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from deploy_diff.entrypoint_tracker import build_entrypoint_report


def _build_entrypoint_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "entrypoint-diff",
        help="Compare ENTRYPOINT and CMD between two image config JSON files.",
    )
    p.add_argument("old_config", help="Path to old image config JSON")
    p.add_argument("new_config", help="Path to new image config JSON")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="fmt",
        help="Output format (default: plain)",
    )
    return p


def build_entrypoint_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy-diff-entrypoint",
        description="Diff ENTRYPOINT/CMD fields between Docker image configs.",
    )
    sub = parser.add_subparsers(dest="command")
    _build_entrypoint_diff_parser(sub)
    return parser


def _load_config(path: str) -> dict:
    data = json.loads(Path(path).read_text())
    # Support both bare config dict and wrapped {"config": {...}}
    return data.get("config", data) if isinstance(data, dict) else data


def cmd_entrypoint_diff(args: argparse.Namespace) -> int:
    try:
        old = _load_config(args.old_config)
        new = _load_config(args.new_config)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    report = build_entrypoint_report(old, new)

    if args.fmt == "json":
        out = {
            "has_changes": report.has_changes,
            "entrypoint": {
                "old": report.entrypoint.old if report.entrypoint else None,
                "new": report.entrypoint.new if report.entrypoint else None,
            },
            "cmd": {
                "old": report.cmd.old if report.cmd else None,
                "new": report.cmd.new if report.cmd else None,
            },
        }
        print(json.dumps(out, indent=2))
    else:
        print(report.summary())

    return 0


def main(argv: Optional[list] = None) -> None:
    parser = build_entrypoint_parser()
    args = parser.parse_args(argv)
    if args.command == "entrypoint-diff":
        sys.exit(cmd_entrypoint_diff(args))
    else:
        parser.print_help()
        sys.exit(0)
