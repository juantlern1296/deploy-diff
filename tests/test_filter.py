"""Tests for deploy_diff.filter."""

import pytest

from deploy_diff.diff_engine import ChangeKind, LayerChange
from deploy_diff.filter import ChangeFilter, FilterError, filter_changes
from deploy_diff.layer_parser import LayerInfo


def _make_change(
    kind: ChangeKind, digest: str = "sha256:abcdef", empty: bool = False
) -> LayerChange:
    layer = LayerInfo(digest=digest, size=100, is_empty=empty)
    return LayerChange(kind=kind, layer=layer)


ADDED = _make_change(ChangeKind.ADDED, "sha256:aaaa")
REMOVED = _make_change(ChangeKind.REMOVED, "sha256:bbbb")
MODIFIED = _make_change(ChangeKind.MODIFIED, "sha256:cccc")
UNCHANGED = _make_change(ChangeKind.UNCHANGED, "sha256:dddd")

ALL_CHANGES = [ADDED, REMOVED, MODIFIED, UNCHANGED]


class TestChangeFilter:
    def test_no_filters_returns_all(self):
        result = ChangeFilter().apply(ALL_CHANGES)
        assert result == ALL_CHANGES

    def test_filter_by_single_kind(self):
        result = ChangeFilter(kinds=[ChangeKind.ADDED]).apply(ALL_CHANGES)
        assert result == [ADDED]

    def test_filter_by_multiple_kinds(self):
        result = ChangeFilter(kinds=[ChangeKind.ADDED, ChangeKind.REMOVED]).apply(ALL_CHANGES)
        assert set(result) == {ADDED, REMOVED}

    def test_include_glob_matches(self):
        result = ChangeFilter(include_glob="sha256:aa*").apply(ALL_CHANGES)
        assert result == [ADDED]

    def test_exclude_glob_removes(self):
        result = ChangeFilter(exclude_glob="sha256:aa*").apply(ALL_CHANGES)
        assert ADDED not in result
        assert len(result) == 3

    def test_include_regex_matches(self):
        result = ChangeFilter(include_regex=r"bb|cc").apply(ALL_CHANGES)
        assert set(result) == {REMOVED, MODIFIED}

    def test_invalid_regex_raises(self):
        with pytest.raises(FilterError):
            ChangeFilter(include_regex="[invalid")

    def test_combined_kind_and_glob(self):
        result = ChangeFilter(
            kinds=[ChangeKind.ADDED, ChangeKind.REMOVED],
            include_glob="sha256:aa*",
        ).apply(ALL_CHANGES)
        assert result == [ADDED]

    def test_empty_input(self):
        assert ChangeFilter().apply([]) == []


class TestFilterChangesConvenience:
    def test_delegates_correctly(self):
        result = filter_changes(ALL_CHANGES, kinds=[ChangeKind.UNCHANGED])
        assert result == [UNCHANGED]

    def test_no_args_returns_all(self):
        assert filter_changes(ALL_CHANGES) == ALL_CHANGES
