"""Tests for label_tracker and label_cli."""

from __future__ import annotations

import json
import pytest

from deploy_diff.label_tracker import LabelDelta, LabelReport, diff_labels
from deploy_diff.label_cli import cmd_label_diff, _parse_labels


# ---------------------------------------------------------------------------
# LabelDelta
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = LabelDelta(key="env", old_value=None, new_value="prod")
    assert str(d) == "+ env=prod"


def test_delta_str_removed():
    d = LabelDelta(key="env", old_value="staging", new_value=None)
    assert str(d) == "- env=staging"


def test_delta_str_modified():
    d = LabelDelta(key="version", old_value="1.0", new_value="2.0")
    assert str(d) == "~ version: '1.0' -> '2.0'"


def test_is_added_flag():
    d = LabelDelta(key="k", old_value=None, new_value="v")
    assert d.is_added
    assert not d.is_removed
    assert not d.is_modified


def test_is_removed_flag():
    d = LabelDelta(key="k", old_value="v", new_value=None)
    assert d.is_removed


def test_is_modified_flag():
    d = LabelDelta(key="k", old_value="a", new_value="b")
    assert d.is_modified


# ---------------------------------------------------------------------------
# diff_labels
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty_report():
    report = diff_labels({"a": "1"}, {"a": "1"})
    assert report.is_empty()
    assert report.total == 0


def test_added_label_detected():
    report = diff_labels({}, {"new_key": "val"})
    assert report.total == 1
    assert len(report.added) == 1
    assert report.added[0].key == "new_key"


def test_removed_label_detected():
    report = diff_labels({"gone": "bye"}, {})
    assert len(report.removed) == 1


def test_modified_label_detected():
    report = diff_labels({"ver": "1"}, {"ver": "2"})
    assert len(report.modified) == 1
    assert report.modified[0].new_value == "2"


def test_mixed_changes():
    old = {"a": "1", "b": "2"}
    new = {"b": "99", "c": "3"}
    report = diff_labels(old, new)
    assert len(report.added) == 1
    assert len(report.removed) == 1
    assert len(report.modified) == 1


def test_deltas_sorted_by_key():
    report = diff_labels({}, {"z": "1", "a": "2", "m": "3"})
    keys = [d.key for d in report.deltas]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_parse_labels_valid():
    raw = json.dumps({"key": "value"})
    result = _parse_labels(raw)
    assert result == {"key": "value"}


def test_parse_labels_invalid_json_raises():
    with pytest.raises(SystemExit):
        _parse_labels("{not valid}")


def test_parse_labels_non_object_raises():
    with pytest.raises(SystemExit):
        _parse_labels("[1, 2, 3]")


class _Args:
    def __init__(self, old, new, label_format="plain"):
        self.old = old
        self.new = new
        self.label_format = label_format


def test_cmd_label_diff_no_changes(capsys):
    args = _Args(old=json.dumps({"k": "v"}), new=json.dumps({"k": "v"}))
    rc = cmd_label_diff(args)
    assert rc == 0
    assert "No label changes" in capsys.readouterr().out


def test_cmd_label_diff_plain_output(capsys):
    args = _Args(old=json.dumps({}), new=json.dumps({"env": "prod"}))
    rc = cmd_label_diff(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "env=prod" in out


def test_cmd_label_diff_json_output(capsys):
    args = _Args(
        old=json.dumps({"v": "1"}),
        new=json.dumps({"v": "2"}),
        label_format="json",
    )
    rc = cmd_label_diff(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["key"] == "v"
