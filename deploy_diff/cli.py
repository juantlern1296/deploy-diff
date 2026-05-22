"""Minimal CLI entry point for deploy-diff."""

import argparse
import json
import sys

from .layer_parser import parse_image_config
from .diff_engine import diff_layers
from .formatter import format_changelog


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="deploy-diff",
        description="Generate a human-readable changelog between two Docker image configs.",
    )
    p.add_argument("base", help="Path to base image config JSON (or '-' for stdin)")
    p.add_argument("target", help="Path to target image config JSON")
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        default=False,
        help="Output diff as JSON instead of human-readable text",
    )
    return p


def _load(path: str) -> dict:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_cfg = _load(args.base)
        target_cfg = _load(args.target)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"deploy-diff error: {exc}", file=sys.stderr)
        return 1

    base_layers = parse_image_config(base_cfg)
    target_layers = parse_image_config(target_cfg)
    changes = diff_layers(base_layers, target_layers)

    if args.output_json:
        output = [
            {
                "kind": c.kind.value,
                "digest": c.digest,
                "created_by": c.created_by,
                "empty": c.empty,
            }
            for c in changes
        ]
        print(json.dumps(output, indent=2))
    else:
        print(
            format_changelog(
                changes,
                image_from=args.base,
                image_to=args.target,
                color=not args.no_color,
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
