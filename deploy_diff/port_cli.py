"""CLI helpers for the port-tracker feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from deploy_diff.port_tracker import PortReport, build_port_report


def _build_port_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("port-diff", help="Show exposed-port changes between two image configs")
    p.add_argument("old_config", help="Path to old image config JSON")
    p.add_argument("new_config", help="Path to new image config JSON")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    return p


def build_port_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy-diff-ports", description="Port tracker CLI")
    sub = parser.add_subparsers(dest="command")
    _build_port_diff_parser(sub)
    return parser


def _load_config(path: str) -> dict:
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot load {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_port_diff(args: argparse.Namespace) -> int:
    old_cfg = _load_config(args.old_config)
    new_cfg = _load_config(args.new_config)
    report: PortReport = build_port_report(old_cfg, new_cfg)

    if args.as_json:
        rows = [
            {"port": d.port, "old": d.old_value, "new": d.new_value}
            for d in report.deltas
        ]
        print(json.dumps(rows, indent=2))
    else:
        if not report.has_changes():
            print("No port changes detected.")
        else:
            for delta in report.deltas:
                print(str(delta))
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = build_port_parser()
    args = parser.parse_args(argv)
    if args.command == "port-diff":
        return cmd_port_diff(args)
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
