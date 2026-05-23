"""CLI sub-command: validate a report JSON file against the deploy-diff schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deploy_diff.schema_validator import validate_report


def _build_validate_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("validate", help="Validate a report JSON file")
    p.add_argument("file", help="Path to the report JSON file")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status on any warning",
    )
    p.set_defaults(cmd_func=cmd_validate)


def build_schema_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy-diff-schema",
        description="Schema validation utilities",
    )
    sub = parser.add_subparsers(dest="command")
    _build_validate_parser(sub)
    return parser


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON — {exc}", file=sys.stderr)
        return 2

    result = validate_report(doc)
    if result:
        print(f"✓ {path} is valid")
        return 0

    print(f"✗ {path} is invalid:", file=sys.stderr)
    for err in result.errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


def main() -> None:
    parser = build_schema_parser()
    args = parser.parse_args()
    if not hasattr(args, "cmd_func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.cmd_func(args))


if __name__ == "__main__":
    main()
