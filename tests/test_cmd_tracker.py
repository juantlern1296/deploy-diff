"""Tests for cmd_tracker and cmd_cli."""

from __future__ import annotations

import json
import os
import pytest

from deploy_diff.layer_parser import LayerInfo
from deploy_diff.cmd_tracker import CmdDelta, CmdReport, diff_cmd


def _layer(cmd=None) -> LayerInfo:
    extra = {"Cmd": cmd} if cmd is not None else {}
    return LayerInfo(digest="sha256:abc", is_empty=False, command="", extra=extra)


# --- CmdDelta str ---

def test_delta_str_added():
    d = CmdDelta(old=None, new=["/bin/sh", "-c", "echo hi"])
    assert "added" in str(d)


def test_delta_str_removed():
    d = CmdDelta(old=["/bin/sh"], new=None)
    assert "removed" in str(d)


def test_delta_str_modified():
    d = CmdDelta(old=["/bin/sh"], new=["/bin/bash"])
    assert "->" in str(d)


# --- is_added / is_removed / is_modified ---

def test_is_added_flag():
    d = CmdDelta(old=None, new=["/app"])
    assert d.is_added
    assert not d.is_removed
    assert not d.is_modified


def test_is_removed_flag():
    d = CmdDelta(old=["/app"], new=None)
    assert d.is_removed
    assert not d.is_added


def test_is_modified_flag():
    d = CmdDelta(old=["/app"], new=["/app", "--verbose"])
    assert d.is_modified
    assert not d.is_added
    assert not d.is_removed


# --- diff_cmd ---

def test_no_changes_returns_empty_report():
    old = _layer(["/bin/sh", "-c", "start"])
    new = _layer(["/bin/sh", "-c", "start"])
    report = diff_cmd(old, new)
    assert not report.has_changes
    assert report.delta is None


def test_added_cmd_detected():
    old = _layer()
    new = _layer(["/bin/sh"])
    report = diff_cmd(old, new)
    assert report.has_changes
    assert report.delta.is_added


def test_removed_cmd_detected():
    old = _layer(["/bin/sh"])
    new = _layer()
    report = diff_cmd(old, new)
    assert report.has_changes
    assert report.delta.is_removed


def test_modified_cmd_detected():
    old = _layer(["/bin/sh", "-c", "v1"])
    new = _layer(["/bin/sh", "-c", "v2"])
    report = diff_cmd(old, new)
    assert report.has_changes
    assert report.delta.is_modified


def test_summary_no_changes():
    report = CmdReport(delta=None)
    assert "no changes" in report.summary()


def test_summary_with_delta():
    report = CmdReport(delta=CmdDelta(old=None, new=["/app"]))
    assert "CMD" in report.summary()


def test_string_cmd_coerced_to_list():
    layer = LayerInfo(digest="sha256:abc", is_empty=False, command="", extra={"Cmd": "/bin/sh"})
    other = _layer(["/bin/sh"])
    # string vs list — both normalised; string becomes ['/bin/sh']
    report = diff_cmd(layer, other)
    assert not report.has_changes


def test_none_extra_treated_as_no_cmd():
    layer = LayerInfo(digest="sha256:abc", is_empty=False, command="", extra=None)
    other = _layer()
    report = diff_cmd(layer, other)
    assert not report.has_changes
