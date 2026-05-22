"""CLI helpers for applying change filters from parsed arguments."""

from __future__ import annotations

import argparse
from typing import List, Optional

from deploy_diff.diff_engine import ChangeKind, LayerChange
from deploy_diff.filter import FilterError, filter_changes


def add_filter_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach filter-related flags to *parser*."""
    grp = parser.add_argument_group("filtering")
    grp.add_argument(
        "--kind",
        dest="kinds",
        metavar="KIND",
        action="append",
        choices=[k.value for k in ChangeKind],
        help="Only include changes of this kind (repeatable).",
    )
    grp.add_argument(
        "--include",
        dest="include_glob",
        metavar="GLOB",
        default=None,
        help="Only include layers whose digest matches GLOB.",
    )
    grp.add_argument(
        "--exclude",
        dest="exclude_glob",
        metavar="GLOB",
        default=None,
        help="Exclude layers whose digest matches GLOB.",
    )
    grp.add_argument(
        "--include-regex",
        dest="include_regex",
        metavar="PATTERN",
        default=None,
        help="Only include layers whose digest matches PATTERN (regex).",
    )


def apply_filters_from_args(
    args: argparse.Namespace,
    changes: List[LayerChange],
) -> List[LayerChange]:
    """Read filter flags from *args* and return the filtered change list.

    Raises SystemExit on invalid filter expressions so callers don't need
    to handle :class:`~deploy_diff.filter.FilterError` themselves.
    """
    raw_kinds: Optional[List[str]] = getattr(args, "kinds", None)
    parsed_kinds = [ChangeKind(k) for k in raw_kinds] if raw_kinds else None

    try:
        return filter_changes(
            changes,
            kinds=parsed_kinds,
            include_glob=getattr(args, "include_glob", None),
            exclude_glob=getattr(args, "exclude_glob", None),
            include_regex=getattr(args, "include_regex", None),
        )
    except FilterError as exc:
        raise SystemExit(f"filter error: {exc}") from exc
