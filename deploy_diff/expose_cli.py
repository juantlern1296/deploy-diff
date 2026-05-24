"""CLI commands for diffing EXPOSE declarations between two image layers."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from deploy_diff.expose_tracker import diff_exposed_ports
from deploy_diff.layer_parser import parse_image_config


def _build_expose_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("expose-diff", help="Compare EXPOSE declarations between two image configs")
    p.add_argument("old_config", help="Path to old image config JSON (or '-' for stdin)")
    p.add_argument("new_config", help="Path to new image config JSON")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="output_format",
        help="Output format (default: plain)",
    )
    return p


def build_expose_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy-diff-expose", description="Diff EXPOSE declarations")
    sub = parser.add_subparsers(dest="command")
    _build_expose_diff_parser(sub)
    return parser


def _load_layer(path: str):
    if path == "-":
        data = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = fh.read()
    layers = parse_image_config(data)
    return layers[-1] if layers else None


def cmd_expose_diff(args: argparse.Namespace, out=sys.stdout) -> int:
    old_layer = _load_layer(args.old_config)
    new_layer = _load_layer(args.new_config)
    report = diff_exposed_ports(old_layer, new_layer)

    if report.is_empty():
        print("No changes in exposed ports.", file=out)
        return 0

    if args.output_format == "json":
        payload = [
            {"key": d.key, "old": d.old_value, "new": d.new_value}
            for d in report.deltas
        ]
        print(json.dumps(payload, indent=2), file=out)
    else:
        for delta in report.deltas:
            print(str(delta), file=out)

    return 0


def main(argv=None) -> int:
    parser = build_expose_parser()
    args = parser.parse_args(argv)
    if args.command == "expose-diff":
        return cmd_expose_diff(args)
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
