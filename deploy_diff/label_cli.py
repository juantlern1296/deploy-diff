"""CLI helpers for label tracking sub-commands."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from deploy_diff.label_tracker import diff_labels


def _build_label_diff_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = sub.add_parser("label-diff", help="Compare labels between two images")
    p.add_argument("--old", required=True, help="JSON object of old labels")
    p.add_argument("--new", required=True, help="JSON object of new labels")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="label_format",
    )
    p.set_defaults(cmd=cmd_label_diff)


def build_label_parser(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="label_cmd")
    _build_label_diff_parser(sub)


def _parse_labels(raw: str) -> Dict[str, str]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON for labels: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Labels must be a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def cmd_label_diff(args: argparse.Namespace) -> int:
    old_labels = _parse_labels(args.old)
    new_labels = _parse_labels(args.new)

    report = diff_labels(old_labels, new_labels)

    if report.is_empty():
        print("No label changes detected.")
        return 0

    if args.label_format == "json":
        out = [
            {
                "key": d.key,
                "old": d.old_value,
                "new": d.new_value,
            }
            for d in report.deltas
        ]
        print(json.dumps(out, indent=2))
    else:
        print(f"Label changes ({report.total}):")
        for delta in report.deltas:
            print(f"  {delta}")

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="deploy-diff-labels")
    build_label_parser(parser)
    args = parser.parse_args(argv)
    if not hasattr(args, "cmd"):
        parser.print_help()
        return 1
    return args.cmd(args)


if __name__ == "__main__":
    sys.exit(main())
