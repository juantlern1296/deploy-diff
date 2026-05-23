"""CLI helpers for configuring retry behaviour via argparse arguments."""

from __future__ import annotations

import argparse
from deploy_diff.retry import RetryPolicy


def add_retry_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach --retry-* flags to *parser*."""
    grp = parser.add_argument_group("retry options")
    grp.add_argument(
        "--retry-attempts",
        type=int,
        default=3,
        metavar="N",
        help="Maximum number of attempts (default: %(default)s)",
    )
    grp.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        metavar="SECS",
        help="Initial delay between retries in seconds (default: %(default)s)",
    )
    grp.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        metavar="FACTOR",
        help="Backoff multiplier applied to delay after each failure (default: %(default)s)",
    )


def policy_from_args(args: argparse.Namespace) -> RetryPolicy:
    """Build a :class:`RetryPolicy` from parsed CLI *args*.

    Raises :class:`ValueError` (propagated from :class:`RetryPolicy`) when
    argument values are out of range.
    """
    return RetryPolicy(
        max_attempts=args.retry_attempts,
        delay=args.retry_delay,
        backoff=args.retry_backoff,
    )
