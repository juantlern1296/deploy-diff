"""CLI sub-command for comparing WORKDIR between two image references."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from deploy_diff.image_loader import load_image, ImageLoadError
from deploy_diff.layer_parser import parse_image_config
from deploy_diff.workdir_tracker import build_workdir_report


def _build_workdir_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("workdir-diff", help="Compare WORKDIR between two images")
    p.add_argument("old", help="Old image reference")
    p.add_argument("new", help="New image reference")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="fmt",
        help="Output format (default: plain)",
    )
    return p


def build_workdir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy-diff-workdir")
    sub = parser.add_subparsers(dest="command")
    _build_workdir_diff_parser(sub)
    return parser


def cmd_workdir_diff(args: argparse.Namespace) -> int:
    try:
        old_manifest = load_image(args.old)
        new_manifest = load_image(args.new)
    except ImageLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    old_layers = parse_image_config(old_manifest.config)
    new_layers = parse_image_config(new_manifest.config)
    report = build_workdir_report(old_layers, new_layers)

    if args.fmt == "json":
        payload = {
            "has_change": report.has_change,
            "old": report.delta.old if report.delta else None,
            "new": report.delta.new if report.delta else None,
        }
        print(json.dumps(payload))
    else:
        print(report.summary())

    return 0


def main(argv: List[str] | None = None) -> int:
    parser = build_workdir_parser()
    args = parser.parse_args(argv)
    if args.command == "workdir-diff":
        return cmd_workdir_diff(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
