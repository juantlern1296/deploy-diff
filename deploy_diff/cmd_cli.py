"""CLI entry point for CMD diff."""

from __future__ import annotations

import argparse
import json
import sys

from deploy_diff.cmd_tracker import diff_cmd
from deploy_diff.layer_parser import LayerInfo


def _build_cmd_diff_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("cmd", help="Compare CMD between two image configs")
    p.add_argument("old_config", help="Path to old image config JSON")
    p.add_argument("new_config", help="Path to new image config JSON")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="fmt",
    )
    p.set_defaults(func=cmd_cmd_diff)


def build_cmd_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy-diff-cmd")
    sub = parser.add_subparsers(dest="command")
    _build_cmd_diff_parser(sub)
    return parser


def _load_layer(path: str) -> LayerInfo:
    with open(path) as fh:
        data = json.load(fh)
    return LayerInfo(
        digest=data.get("digest", ""),
        is_empty=data.get("is_empty", False),
        command=data.get("command", ""),
        extra=data.get("extra"),
    )


def cmd_cmd_diff(args: argparse.Namespace) -> int:
    old = _load_layer(args.old_config)
    new = _load_layer(args.new_config)
    report = diff_cmd(old, new)

    if args.fmt == "json":
        payload = {
            "has_changes": report.has_changes,
            "old": report.delta.old if report.delta else None,
            "new": report.delta.new if report.delta else None,
        }
        print(json.dumps(payload))
    else:
        print(report.summary())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_cmd_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
