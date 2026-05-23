"""Filtering utilities for layer changes."""

from __future__ import annotations

import fnmatch
import re
from typing import Iterable, List, Optional, Sequence

from deploy_diff.diff_engine import ChangeKind, LayerChange


class FilterError(ValueError):
    """Raised when a filter expression is invalid."""


class ChangeFilter:
    """Applies include/exclude rules to a sequence of LayerChange objects."""

    def __init__(
        self,
        kinds: Optional[Sequence[ChangeKind]] = None,
        include_glob: Optional[str] = None,
        exclude_glob: Optional[str] = None,
        include_regex: Optional[str] = None,
    ) -> None:
        self.kinds = set(kinds) if kinds else None
        self.include_glob = include_glob
        self.exclude_glob = exclude_glob
        try:
            self._include_re = re.compile(include_regex) if include_regex else None
        except re.error as exc:
            raise FilterError(f"Invalid include_regex: {exc}") from exc

    def matches(self, change: LayerChange) -> bool:
        """Return True if *change* passes all active filter rules."""
        if self.kinds is not None and change.kind not in self.kinds:
            return False

        digest = change.layer.digest or ""

        if self.include_glob and not fnmatch.fnmatch(digest, self.include_glob):
            return False

        if self.exclude_glob and fnmatch.fnmatch(digest, self.exclude_glob):
            return False

        if self._include_re and not self._include_re.search(digest):
            return False

        return True

    def apply(self, changes: Iterable[LayerChange]) -> List[LayerChange]:
        """Return a filtered list of changes."""
        return [c for c in changes if self.matches(c)]

    def is_empty(self) -> bool:
        """Return True if no filter rules are active (all changes would pass)."""
        return (
            self.kinds is None
            and self.include_glob is None
            and self.exclude_glob is None
            and self._include_re is None
        )


def filter_changes(
    changes: Iterable[LayerChange],
    kinds: Optional[Sequence[ChangeKind]] = None,
    include_glob: Optional[str] = None,
    exclude_glob: Optional[str] = None,
    include_regex: Optional[str] = None,
) -> List[LayerChange]:
    """Convenience wrapper around :class:`ChangeFilter`."""
    return ChangeFilter(
        kinds=kinds,
        include_glob=include_glob,
        exclude_glob=exclude_glob,
        include_regex=include_regex,
    ).apply(changes)
