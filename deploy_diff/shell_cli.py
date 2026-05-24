"""CLI sub-command for comparing Shell configurations between two images."""

from __future__ import annotations

import argparse
import json
import sys

from .image_loader import load_image, ImageLoadError
from .layer_parser import parse_image_config
from .shell_tracker import diff_shell


def _build_shell_diff_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = sub.add_parser("shell-diff", help="Compare Shell (Cmd) config between two images")
    p.add_argument("old", help="Old image reference")
    p.add_argument("new", help="New image reference")
    p.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        dest="output_format",
        help="Output format (default: plain)",
    )
    return p


def build_shell_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    _build_shell_diff_parser(sub)


def cmd_shell_diff(args: argparse.Namespace) -> int:
    try:
        old_manifest = load_image(args.old)
        new_manifest = load_image(args.new)
    except ImageLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    old_layer = parse_image_config(old_manifest.config)
    new_layer = parse_image_config(new_manifest.config)

    report = diff_shell(old_layer, new_layer)

    if args.output_format == "json":
        payload = {
            "has_changes": report.has_changes,
            "old": report.delta.old if report.delta else None,
            "new": report.delta.new if report.delta else None,
        }
        print(json.dumps(payload))
    else:
        print(report.summary())

    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Shell diff tool")
    sub = parser.add_subparsers(dest="command")
    build_shell_parser(sub)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(cmd_shell_diff(args))


if __name__ == "__main__":  # pragma: no cover
    main()
