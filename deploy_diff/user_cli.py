"""CLI commands for diffing USER instructions between two image configs."""

from __future__ import annotations

import argparse
import json
import sys

from deploy_diff.user_tracker import diff_users


def _build_user_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("user-diff", help="Compare USER instruction between two images")
    p.add_argument("old_user", nargs="?", default=None, help="USER value of old image")
    p.add_argument("new_user", nargs="?", default=None, help="USER value of new image")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="fmt",
        help="Output format (default: plain)",
    )
    return p


def build_user_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy-diff-user",
        description="Diff USER instructions in Docker image configs",
    )
    sub = parser.add_subparsers(dest="command")
    _build_user_diff_parser(sub)
    return parser


def cmd_user_diff(args: argparse.Namespace) -> int:
    report = diff_users(args.old_user, args.new_user)

    if args.fmt == "json":
        data = {
            "has_changes": report.has_changes,
            "old_user": report.delta.old_user if report.delta else None,
            "new_user": report.delta.new_user if report.delta else None,
            "summary": report.summary(),
        }
        print(json.dumps(data))
    else:
        print(report.summary())

    return 0


def main(argv=None) -> None:
    parser = build_user_parser()
    args = parser.parse_args(argv)
    if args.command == "user-diff":
        sys.exit(cmd_user_diff(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
