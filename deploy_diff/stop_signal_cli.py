"""CLI interface for the stop-signal tracker."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from deploy_diff.layer_parser import LayerInfo
from deploy_diff.stop_signal_tracker import diff_stop_signal


def _build_stop_signal_diff_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "stop-signal",
        help="Compare STOPSIGNAL between two image configs",
    )
    p.add_argument("old_config", help="Path to old image config JSON")
    p.add_argument("new_config", help="Path to new image config JSON")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="fmt",
    )
    p.set_defaults(func=cmd_stop_signal_diff)


def build_stop_signal_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy-diff-stop-signal",
        description="Diff STOPSIGNAL between two image configs",
    )
    sub = parser.add_subparsers(dest="command")
    _build_stop_signal_diff_parser(sub)
    return parser


def _load_layers(path: str) -> List[LayerInfo]:
    import json as _json
    from deploy_diff.layer_parser import parse_image_config

    with open(path, "r", encoding="utf-8") as fh:
        data = _json.load(fh)
    return parse_image_config(data)


def cmd_stop_signal_diff(args: argparse.Namespace) -> int:
    old_layers = _load_layers(args.old_config)
    new_layers = _load_layers(args.new_config)
    report = diff_stop_signal(old_layers, new_layers)

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


def main() -> None:
    parser = build_stop_signal_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
