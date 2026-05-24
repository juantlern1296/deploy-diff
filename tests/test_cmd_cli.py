"""Tests for cmd_cli."""

from __future__ import annotations

import argparse
import json
import os
import pytest

from deploy_diff.cmd_cli import cmd_cmd_diff, build_cmd_parser


def _write(tmp_path, name, cmd):
    data = {"digest": "sha256:abc", "is_empty": False, "command": "", "extra": {}}
    if cmd is not None:
        data["extra"]["Cmd"] = cmd
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


class _Args:
    def __init__(self, old, new, fmt="plain"):
        self.old_config = old
        self.new_config = new
        self.fmt = fmt


def test_no_changes_plain(tmp_path, capsys):
    old = _write(tmp_path, "old.json", ["/bin/sh"])
    new = _write(tmp_path, "new.json", ["/bin/sh"])
    rc = cmd_cmd_diff(_Args(old, new))
    out = capsys.readouterr().out
    assert rc == 0
    assert "no changes" in out


def test_added_cmd_plain(tmp_path, capsys):
    old = _write(tmp_path, "old.json", None)
    new = _write(tmp_path, "new.json", ["/app"])
    rc = cmd_cmd_diff(_Args(old, new))
    out = capsys.readouterr().out
    assert rc == 0
    assert "CMD" in out


def test_removed_cmd_plain(tmp_path, capsys):
    old = _write(tmp_path, "old.json", ["/app"])
    new = _write(tmp_path, "new.json", None)
    rc = cmd_cmd_diff(_Args(old, new))
    out = capsys.readouterr().out
    assert "removed" in out


def test_json_output(tmp_path, capsys):
    old = _write(tmp_path, "old.json", ["/bin/sh"])
    new = _write(tmp_path, "new.json", ["/bin/bash"])
    rc = cmd_cmd_diff(_Args(old, new, fmt="json"))
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["has_changes"] is True
    assert payload["old"] == ["/bin/sh"]
    assert payload["new"] == ["/bin/bash"]


def test_json_no_changes(tmp_path, capsys):
    old = _write(tmp_path, "old.json", ["/bin/sh"])
    new = _write(tmp_path, "new.json", ["/bin/sh"])
    cmd_cmd_diff(_Args(old, new, fmt="json"))
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["has_changes"] is False
    assert payload["old"] is None
    assert payload["new"] is None


def test_build_parser_returns_parser():
    parser = build_cmd_parser()
    assert isinstance(parser, argparse.ArgumentParser)
