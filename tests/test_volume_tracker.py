"""Tests for volume_tracker and volume_cli."""

from __future__ import annotations

import argparse
import json
import os
import pytest

from deploy_diff.volume_tracker import VolumeDelta, VolumeReport, diff_volumes
from deploy_diff.volume_cli import cmd_volume_diff


# ---------------------------------------------------------------------------
# VolumeDelta helpers
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = VolumeDelta(path="/data", old=None, new="/data")
    assert str(d) == "+ /data"


def test_delta_str_removed():
    d = VolumeDelta(path="/data", old="/data", new=None)
    assert str(d) == "- /data"


def test_is_added_flag():
    d = VolumeDelta(path="/data", old=None, new="/data")
    assert d.is_added() is True
    assert d.is_removed() is False


def test_is_removed_flag():
    d = VolumeDelta(path="/data", old="/data", new=None)
    assert d.is_removed() is True
    assert d.is_added() is False


# ---------------------------------------------------------------------------
# diff_volumes
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty_report():
    cfg = {"Volumes": {"/data": {}}}
    report = diff_volumes(cfg, cfg)
    assert report.is_empty()
    assert report.total == 0


def test_added_volume_detected():
    old = {"Volumes": {}}
    new = {"Volumes": {"/cache": {}}}
    report = diff_volumes(old, new)
    assert report.total == 1
    assert report.added[0].path == "/cache"


def test_removed_volume_detected():
    old = {"Volumes": {"/cache": {}}}
    new = {"Volumes": {}}
    report = diff_volumes(old, new)
    assert report.total == 1
    assert report.removed[0].path == "/cache"


def test_none_volumes_field_treated_as_empty():
    old = {"Volumes": None}
    new = {"Volumes": {"/tmp": {}}}
    report = diff_volumes(old, new)
    assert report.total == 1
    assert report.added[0].path == "/tmp"


def test_missing_volumes_key_treated_as_empty():
    report = diff_volumes({}, {})
    assert report.is_empty()


def test_multiple_deltas_sorted():
    old = {"Volumes": {"/b": {}, "/a": {}}}
    new = {"Volumes": {"/b": {}, "/c": {}}}
    report = diff_volumes(old, new)
    paths = [d.path for d in report.deltas]
    assert paths == sorted(paths)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write_config(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


def test_no_changes_plain(tmp_path, capsys):
    cfg = _write_config(tmp_path, "cfg.json", {"Volumes": {"/data": {}}})
    args = argparse.Namespace(old_config=cfg, new_config=cfg, fmt="plain")
    rc = cmd_volume_diff(args)
    assert rc == 0
    assert "No volume changes" in capsys.readouterr().out


def test_added_volume_plain(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {})
    new = _write_config(tmp_path, "new.json", {"Volumes": {"/mnt": {}}})
    args = argparse.Namespace(old_config=old, new_config=new, fmt="plain")
    rc = cmd_volume_diff(args)
    assert rc == 0
    assert "+ /mnt" in capsys.readouterr().out


def test_json_output(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {"Volumes": {"/data": {}}})
    new = _write_config(tmp_path, "new.json", {})
    args = argparse.Namespace(old_config=old, new_config=new, fmt="json")
    rc = cmd_volume_diff(args)
    assert rc == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["path"] == "/data"


def test_missing_file_returns_error(tmp_path, capsys):
    args = argparse.Namespace(old_config="/no/such/file.json", new_config="/no/such/file2.json", fmt="plain")
    rc = cmd_volume_diff(args)
    assert rc == 1
