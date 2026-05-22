"""CLI sub-commands for managing notification hooks at runtime.

Exposes:
  deploy-diff notify log    -- fire the built-in log hook against a cached report
  deploy-diff notify list   -- list registered hooks
"""

from __future__ import annotations

import argparse
import json
import sys

from deploy_diff.notifier import list_hooks, notify_all, NotifierError
from deploy_diff.builtin_notifiers import register_log_hook, register_slack_hook
from deploy_diff.reporter import Report


def _build_notify_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("notify", help="Manage and fire notification hooks")
    ns = p.add_subparsers(dest="notify_cmd", required=True)

    # list
    ns.add_parser("list", help="List registered hooks")

    # fire
    fire_p = ns.add_parser("fire", help="Fire all hooks against a JSON report file")
    fire_p.add_argument("report", help="Path to a JSON report produced by deploy-diff")
    fire_p.add_argument(
        "--slack-webhook",
        metavar="URL",
        help="Register a Slack webhook before firing",
    )
    fire_p.add_argument(
        "--log",
        action="store_true",
        help="Register the built-in log hook before firing",
    )
    fire_p.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit non-zero on first hook error",
    )


def cmd_notify(args: argparse.Namespace) -> int:
    """Dispatch notify sub-commands. Returns exit code."""
    if args.notify_cmd == "list":
        hooks = list_hooks()
        if hooks:
            for name in hooks:
                print(name)
        else:
            print("(no hooks registered)")
        return 0

    if args.notify_cmd == "fire":
        # Optionally register built-ins
        if getattr(args, "log", False):
            try:
                register_log_hook()
            except NotifierError:
                pass  # already registered

        slack_url = getattr(args, "slack_webhook", None)
        if slack_url:
            try:
                register_slack_hook(slack_url)
            except NotifierError:
                pass

        # Load report from JSON file
        try:
            with open(args.report) as fh:
                data = json.load(fh)
            report = Report(**data)  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            print(f"error: could not load report: {exc}", file=sys.stderr)
            return 2

        errors = notify_all(report, raise_on_error=args.fail_fast)
        if errors:
            for name, exc in errors.items():
                print(f"hook '{name}' failed: {exc}", file=sys.stderr)
            return 1
        return 0

    print(f"Unknown notify command: {args.notify_cmd}", file=sys.stderr)
    return 2
