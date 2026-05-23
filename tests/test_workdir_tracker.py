"""Tests for workdir_tracker and workdir_cli."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from deploy_diff.layer_parser import LayerInfo
from deploy_diff.workdir_tracker import (
    WorkdirDelta,
    WorkdirReport,
    build_workdir_report,
    _extract_workdir,
)


def _layer(cmd: str | None = None, empty: bool = False) -> LayerInfo:
    return LayerInfo(digest="sha256:abc", command=cmd, is_empty=empty)


# --- WorkdirDelta ---

def test_delta_str_added():
    d = WorkdirDelta(old=None, new="/app")
    assert str(d) == "+ WORKDIR /app"


def test_delta_str_removed():
    d = WorkdirDelta(old="/app", new=None)
    assert str(d) == "- WORKDIR /app"


def test_delta_str_modified():
    d = WorkdirDelta(old="/app", new="/srv")
    assert str(d) == "~ WORKDIR /app -> /srv"


def test_is_added_flag():
    assert WorkdirDelta(old=None, new="/app").is_added is True
    assert WorkdirDelta(old="/app", new="/srv").is_added is False


def test_is_removed_flag():
    assert WorkdirDelta(old="/app", new=None).is_removed is True
    assert WorkdirDelta(old=None, new="/app").is_removed is False


def test_is_modified_flag():
    assert WorkdirDelta(old="/app", new="/srv").is_modified is True
    assert WorkdirDelta(old="/app", new="/app").is_modified is False


# --- _extract_workdir ---

def test_extract_returns_none_when_no_workdir():
    layers = [_layer("RUN apt-get update"), _layer("COPY . .")]
    assert _extract_workdir(layers) is None


def test_extract_returns_last_workdir():
    layers = [_layer("WORKDIR /first"), _layer("WORKDIR /second")]
    assert _extract_workdir(layers) == "/second"


def test_extract_case_insensitive():
    layers = [_layer("workdir /lower")]
    assert _extract_workdir(layers) == "/lower"


# --- build_workdir_report ---

def test_no_change_returns_none_delta():
    old = [_layer("WORKDIR /app")]
    new = [_layer("WORKDIR /app")]
    report = build_workdir_report(old, new)
    assert report.delta is None
    assert report.has_change is False


def test_added_workdir():
    old: list = []
    new = [_layer("WORKDIR /app")]
    report = build_workdir_report(old, new)
    assert report.has_change is True
    assert report.delta is not None
    assert report.delta.is_added


def test_removed_workdir():
    old = [_layer("WORKDIR /app")]
    new: list = []
    report = build_workdir_report(old, new)
    assert report.delta is not None
    assert report.delta.is_removed


def test_modified_workdir():
    old = [_layer("WORKDIR /app")]
    new = [_layer("WORKDIR /srv")]
    report = build_workdir_report(old, new)
    assert report.delta is not None
    assert report.delta.is_modified
    assert report.summary() == "~ WORKDIR /app -> /srv"


def test_summary_unchanged():
    report = WorkdirReport(delta=None)
    assert report.summary() == "WORKDIR unchanged"
