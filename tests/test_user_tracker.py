"""Tests for user_tracker and user_cli."""

from __future__ import annotations

import argparse
import json
from io import StringIO
from unittest.mock import patch

import pytest

from deploy_diff.user_tracker import UserDelta, UserReport, diff_users, build_user_report
from deploy_diff.diff_engine import LayerChange, ChangeKind
from deploy_diff.user_cli import cmd_user_diff, build_user_parser


# ---------------------------------------------------------------------------
# UserDelta
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = UserDelta(old_user=None, new_user="appuser")
    assert "added" in str(d)
    assert "appuser" in str(d)


def test_delta_str_removed():
    d = UserDelta(old_user="root", new_user=None)
    assert "removed" in str(d)
    assert "root" in str(d)


def test_delta_str_modified():
    d = UserDelta(old_user="root", new_user="nobody")
    assert "root" in str(d)
    assert "nobody" in str(d)


def test_is_added_flag():
    assert UserDelta(old_user=None, new_user="app").is_added
    assert not UserDelta(old_user="root", new_user="app").is_added


def test_is_removed_flag():
    assert UserDelta(old_user="root", new_user=None).is_removed
    assert not UserDelta(old_user=None, new_user="app").is_removed


def test_is_modified_flag():
    assert UserDelta(old_user="root", new_user="nobody").is_modified
    assert not UserDelta(old_user=None, new_user="app").is_modified


# ---------------------------------------------------------------------------
# diff_users
# ---------------------------------------------------------------------------

def test_no_change_returns_no_delta():
    report = diff_users("appuser", "appuser")
    assert not report.has_changes
    assert report.delta is None


def test_added_user():
    report = diff_users(None, "appuser")
    assert report.has_changes
    assert report.delta.is_added


def test_removed_user():
    report = diff_users("root", None)
    assert report.has_changes
    assert report.delta.is_removed


def test_modified_user():
    report = diff_users("root", "nobody")
    assert report.has_changes
    assert report.delta.is_modified


def test_summary_no_changes():
    report = diff_users("app", "app")
    assert "No USER changes" in report.summary()


# ---------------------------------------------------------------------------
# build_user_report
# ---------------------------------------------------------------------------

def _change(kind, label, old=None, new=None):
    return LayerChange(kind=kind, label=label, old_value=old, new_value=new)


def test_build_report_no_user_changes():
    changes = [_change(ChangeKind.ADDED, "env", new="PATH=/usr/bin")]
    report = build_user_report(changes)
    assert not report.has_changes


def test_build_report_added_user():
    changes = [_change(ChangeKind.ADDED, "user", new="appuser")]
    report = build_user_report(changes)
    assert report.has_changes
    assert report.delta.new_user == "appuser"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _args(old=None, new=None, fmt="plain"):
    ns = argparse.Namespace(old_user=old, new_user=new, fmt=fmt)
    return ns


def test_cli_plain_no_change(capsys):
    cmd_user_diff(_args("app", "app"))
    out = capsys.readouterr().out
    assert "No USER changes" in out


def test_cli_plain_modified(capsys):
    cmd_user_diff(_args("root", "nobody"))
    out = capsys.readouterr().out
    assert "nobody" in out


def test_cli_json_output(capsys):
    cmd_user_diff(_args("root", "app", fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["has_changes"] is True
    assert data["new_user"] == "app"


def test_cli_returns_zero():
    assert cmd_user_diff(_args("root", "app")) == 0
