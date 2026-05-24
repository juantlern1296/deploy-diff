"""Tests for stop_signal_tracker and stop_signal_cli."""

from __future__ import annotations

import json
import io
import sys
from typing import List, Optional
from unittest.mock import patch

import pytest

from deploy_diff.layer_parser import LayerInfo
from deploy_diff.stop_signal_tracker import (
    StopSignalDelta,
    StopSignalReport,
    diff_stop_signal,
)


def _layer(signal: Optional[str] = None) -> LayerInfo:
    config = {}
    if signal is not None:
        config["StopSignal"] = signal
    return LayerInfo(digest="sha256:aabbcc", is_empty=False, command="RUN x", config=config)


# ---------------------------------------------------------------------------
# StopSignalDelta
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = StopSignalDelta(old=None, new="SIGTERM")
    assert "added" in str(d)
    assert "SIGTERM" in str(d)


def test_delta_str_removed():
    d = StopSignalDelta(old="SIGKILL", new=None)
    assert "removed" in str(d)
    assert "SIGKILL" in str(d)


def test_delta_str_modified():
    d = StopSignalDelta(old="SIGTERM", new="SIGKILL")
    assert "->" in str(d)


def test_is_added_flag():
    assert StopSignalDelta(old=None, new="SIGTERM").is_added
    assert not StopSignalDelta(old="SIGTERM", new="SIGKILL").is_added


def test_is_removed_flag():
    assert StopSignalDelta(old="SIGTERM", new=None).is_removed
    assert not StopSignalDelta(old=None, new="SIGTERM").is_removed


def test_is_modified_flag():
    assert StopSignalDelta(old="SIGTERM", new="SIGKILL").is_modified
    assert not StopSignalDelta(old=None, new="SIGTERM").is_modified


# ---------------------------------------------------------------------------
# diff_stop_signal
# ---------------------------------------------------------------------------

def test_no_changes_returns_no_delta():
    old = [_layer("SIGTERM")]
    new = [_layer("SIGTERM")]
    report = diff_stop_signal(old, new)
    assert not report.has_changes
    assert report.delta is None


def test_added_signal_detected():
    old: List[LayerInfo] = [_layer()]
    new = [_layer("SIGTERM")]
    report = diff_stop_signal(old, new)
    assert report.has_changes
    assert report.delta is not None
    assert report.delta.is_added


def test_removed_signal_detected():
    old = [_layer("SIGKILL")]
    new = [_layer()]
    report = diff_stop_signal(old, new)
    assert report.has_changes
    assert report.delta.is_removed  # type: ignore[union-attr]


def test_modified_signal_detected():
    old = [_layer("SIGTERM")]
    new = [_layer("SIGKILL")]
    report = diff_stop_signal(old, new)
    assert report.has_changes
    assert report.delta.is_modified  # type: ignore[union-attr]


def test_last_layer_wins():
    old = [_layer("SIGTERM"), _layer("SIGKILL")]
    new = [_layer("SIGKILL"), _layer("SIGTERM")]
    report = diff_stop_signal(old, new)
    assert report.delta.old == "SIGKILL"  # type: ignore[union-attr]
    assert report.delta.new == "SIGTERM"  # type: ignore[union-attr]


def test_both_empty_no_changes():
    report = diff_stop_signal([_layer()], [_layer()])
    assert not report.has_changes


def test_summary_no_changes():
    r = StopSignalReport(delta=None)
    assert "no changes" in r.summary()


def test_summary_with_changes():
    r = StopSignalReport(delta=StopSignalDelta(old=None, new="SIGTERM"))
    assert "SIGTERM" in r.summary()
