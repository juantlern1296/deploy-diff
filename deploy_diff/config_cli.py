"""CLI sub-commands for inspecting and validating deploy-diff configuration."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deploy_diff.config import ConfigError, load_config


def _build_show_parser(sub: argparse.Action) -> None:
    p = sub.add_parser("show", help="Print resolved configuration as JSON")
    p.add_argument(
        "--config", metavar="FILE", help="Path to config JSON file"
    )


def _build_check_parser(sub: argparse.Action) -> None:
    p = sub.add_parser("check", help="Validate a configuration file")
    p.add_argument("file", metavar="FILE", help="Config file to validate")


def build_config_parser(parent: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = parent.add_parser("config", help="Manage deploy-diff configuration")
    sub = p.add_subparsers(dest="config_cmd", required=True)
    _build_show_parser(sub)
    _build_check_parser(sub)
    p.set_defaults(func=cmd_config)


def cmd_config(args: argparse.Namespace) -> int:
    if args.config_cmd == "show":
        return _cmd_show(args)
    if args.config_cmd == "check":
        return _cmd_check(args)
    return 1


def _cmd_show(args: argparse.Namespace) -> int:
    path = Path(args.config) if getattr(args, "config", None) else None
    try:
        cfg = load_config(path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = {
        "cache_dir": str(cfg.cache_dir),
        "snapshot_dir": str(cfg.snapshot_dir),
        "audit_dir": str(cfg.audit_dir),
        "default_output_format": cfg.default_output_format,
        "max_retry_attempts": cfg.max_retry_attempts,
        "retry_delay": cfg.retry_delay,
        "log_level": cfg.log_level,
        "extra": cfg.extra,
    }
    print(json.dumps(out, indent=2))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        load_config(path)
        print(f"OK: {path} is valid")
        return 0
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
