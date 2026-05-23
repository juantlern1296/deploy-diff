"""CLI sub-command for comparing Docker image volume mounts."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from deploy_diff.volume_tracker import diff_volumes


def _build_volume_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("volume-diff", help="Compare volume mounts between two image configs")
    p.add_argument("old_config", help="Path to old image config JSON file")
    p.add_argument("new_config", help="Path to new image config JSON file")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="fmt",
        help="Output format (default: plain)",
    )
    return p


def build_volume_parser(sub: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    if sub is None:
        parser = argparse.ArgumentParser(prog="deploy-diff volume-diff")
        sub = parser.add_subparsers()
    _build_volume_diff_parser(sub)
    return sub


def _load_config(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def cmd_volume_diff(args: argparse.Namespace) -> int:
    try:
        old_cfg = _load_config(args.old_config)
        new_cfg = _load_config(args.new_config)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    report = diff_volumes(old_cfg, new_cfg)

    if args.fmt == "json":
        rows = [
            {"path": d.path, "old": d.old, "new": d.new}
            for d in report.deltas
        ]
        print(json.dumps(rows, indent=2))
    else:
        if report.is_empty():
            print("No volume changes.")
        else:
            for delta in report.deltas:
                print(str(delta))

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="deploy-diff-volumes")
    parser.add_argument("old_config")
    parser.add_argument("new_config")
    parser.add_argument("--format", choices=["plain", "json"], default="plain", dest="fmt")
    args = parser.parse_args()
    sys.exit(cmd_volume_diff(args))
