"""Tests for shell_tracker and shell_cli."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from deploy_diff.layer_parser import LayerInfo
from deploy_diff.shell_tracker import ShellDelta, ShellReport, diff_shell


def _layer(shell=None) -> LayerInfo:
    config = {}
    if shell is not None:
        config["Shell"] = shell
    return LayerInfo(
        digest="sha256:aabbcc",
        is_empty=False,
        command="RUN test",
        config=config,
    )


# --- ShellDelta ---

def test_delta_str_added():
    d = ShellDelta(old=None, new=["/bin/sh", "-c"])
    assert "added" in str(d)
    assert "/bin/sh" in str(d)


def test_delta_str_removed():
    d = ShellDelta(old=["/bin/sh", "-c"], new=None)
    assert "removed" in str(d)


def test_delta_str_modified():
    d = ShellDelta(old=["/bin/sh", "-c"], new=["/bin/bash", "-c"])
    assert "->" in str(d)


def test_is_added_flag():
    d = ShellDelta(old=None, new=["/bin/sh"])
    assert d.is_added
    assert not d.is_removed
    assert not d.is_modified


def test_is_removed_flag():
    d = ShellDelta(old=["/bin/sh"], new=None)
    assert d.is_removed
    assert not d.is_added


def test_is_modified_flag():
    d = ShellDelta(old=["/bin/sh"], new=["/bin/bash"])
    assert d.is_modified
    assert not d.is_added
    assert not d.is_removed


# --- diff_shell ---

def test_no_changes_returns_empty_report():
    old = _layer(["/bin/sh", "-c"])
    new = _layer(["/bin/sh", "-c"])
    report = diff_shell(old, new)
    assert not report.has_changes
    assert report.delta is None


def test_both_none_returns_empty_report():
    report = diff_shell(_layer(), _layer())
    assert not report.has_changes


def test_added_shell_detected():
    report = diff_shell(_layer(), _layer(["/bin/bash", "-c"]))
    assert report.has_changes
    assert report.delta.is_added


def test_removed_shell_detected():
    report = diff_shell(_layer(["/bin/sh"]), _layer())
    assert report.has_changes
    assert report.delta.is_removed


def test_modified_shell_detected():
    report = diff_shell(_layer(["/bin/sh"]), _layer(["/bin/bash"]))
    assert report.has_changes
    assert report.delta.is_modified


# --- ShellReport.summary ---

def test_summary_no_changes():
    r = ShellReport(delta=None)
    assert "no changes" in r.summary()


def test_summary_with_changes():
    d = ShellDelta(old=["/bin/sh"], new=["/bin/bash"])
    r = ShellReport(delta=d)
    assert "shell" in r.summary()
