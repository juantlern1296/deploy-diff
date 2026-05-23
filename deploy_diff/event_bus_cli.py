"""CLI helpers for inspecting the event bus (for debugging / diagnostics)."""

from __future__ import annotations

import argparse
import sys
from typing import List

from deploy_diff import event_bus


def _build_list_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("list", help="List subscribed handlers for an event.")
    p.add_argument("event_name", help="Event name to inspect.")
    p.set_defaults(func=_cmd_list)


def _build_publish_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("publish", help="Publish a test event (dry-run / debug).")
    p.add_argument("event_name", help="Event name to publish.")
    p.add_argument("--source", default="cli", help="Source label for the event.")
    p.set_defaults(func=_cmd_publish)


def build_event_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy-diff events",
        description="Inspect or test the internal event bus.",
    )
    sub = parser.add_subparsers(dest="event_cmd", required=True)
    _build_list_parser(sub)
    _build_publish_parser(sub)
    return parser


def _cmd_list(args: argparse.Namespace) -> int:
    handlers = event_bus.list_subscriptions(args.event_name)
    if not handlers:
        print(f"No handlers registered for {args.event_name!r}.")
        return 0
    print(f"Handlers for {args.event_name!r} ({len(handlers)}):")
    for h in handlers:
        print(f"  - {h.__module__}.{h.__qualname__}")
    return 0


def _cmd_publish(args: argparse.Namespace) -> int:
    count = event_bus.publish(args.event_name, payload=None, source=args.source)
    print(f"Published {args.event_name!r} — {count} handler(s) called.")
    return 0


def main(argv: List[str] | None = None) -> int:  # pragma: no cover
    parser = build_event_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
