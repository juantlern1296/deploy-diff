"""Tests for deploy_diff.env_tracker."""

import pytest

from deploy_diff.diff_engine import ChangeKind
from deploy_diff.env_tracker import EnvDelta, EnvReport, _parse_env_list, build_env_report


# ---------------------------------------------------------------------------
# _parse_env_list
# ---------------------------------------------------------------------------

def test_parse_simple_key_value():
    result = _parse_env_list(["FOO=bar", "BAZ=qux"])
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_value_with_equals():
    result = _parse_env_list(["URL=http://example.com/path?a=1"])
    assert result["URL"] == "http://example.com/path?a=1"


def test_parse_key_without_value():
    result = _parse_env_list(["EMPTY"])
    assert result == {"EMPTY": ""}


def test_parse_empty_list():
    assert _parse_env_list([]) == {}


# ---------------------------------------------------------------------------
# build_env_report — basic cases
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty_report():
    env = ["FOO=bar", "BAZ=1"]
    report = build_env_report(env, env)
    assert report.is_empty()
    assert report.total == 0


def test_added_variable_detected():
    report = build_env_report([], ["NEW_VAR=hello"])
    assert report.total == 1
    delta = report.added[0]
    assert delta.key == "NEW_VAR"
    assert delta.kind == ChangeKind.ADDED
    assert delta.new_value == "hello"
    assert delta.old_value is None


def test_removed_variable_detected():
    report = build_env_report(["OLD=gone"], [])
    assert len(report.removed) == 1
    delta = report.removed[0]
    assert delta.key == "OLD"
    assert delta.kind == ChangeKind.REMOVED
    assert delta.old_value == "gone"


def test_modified_variable_detected():
    report = build_env_report(["VER=1"], ["VER=2"])
    assert len(report.modified) == 1
    delta = report.modified[0]
    assert delta.kind == ChangeKind.MODIFIED
    assert delta.old_value == "1"
    assert delta.new_value == "2"


def test_mixed_changes():
    old = ["KEEP=same", "REMOVE=bye", "CHANGE=old"]
    new = ["KEEP=same", "CHANGE=new", "ADD=hi"]
    report = build_env_report(old, new)
    assert len(report.added) == 1
    assert len(report.removed) == 1
    assert len(report.modified) == 1
    assert report.total == 3


# ---------------------------------------------------------------------------
# EnvDelta __str__
# ---------------------------------------------------------------------------

def test_str_added():
    d = EnvDelta("FOO", ChangeKind.ADDED, new_value="bar")
    assert str(d) == "+ FOO=bar"


def test_str_removed():
    d = EnvDelta("FOO", ChangeKind.REMOVED, old_value="bar")
    assert str(d) == "- FOO=bar"


def test_str_modified():
    d = EnvDelta("FOO", ChangeKind.MODIFIED, old_value="1", new_value="2")
    assert str(d) == "~ FOO: '1' -> '2'"


# ---------------------------------------------------------------------------
# EnvReport helpers
# ---------------------------------------------------------------------------

def test_report_is_empty_true_when_no_deltas():
    assert EnvReport().is_empty()


def test_report_is_empty_false_when_has_deltas():
    d = EnvDelta("X", ChangeKind.ADDED, new_value="y")
    assert not EnvReport(deltas=[d]).is_empty()
