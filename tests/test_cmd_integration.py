"""Integration-style tests for cmd_tracker + cmd_cli together."""

from __future__ import annotations

import json
import pytest

from deploy_diff.layer_parser import LayerInfo
from deploy_diff.cmd_tracker import diff_cmd, CmdReport
from deploy_diff.cmd_cli import cmd_cmd_diff


def _layer(cmd=None) -> LayerInfo:
    extra = {"Cmd": cmd} if cmd is not None else {}
    return LayerInfo(digest="sha256:xyz", is_empty=False, command="", extra=extra)


def _write(tmp_path, name, cmd):
    data = {"digest": "sha256:xyz", "is_empty": False, "command": "", "extra": {}}
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


def test_roundtrip_no_change(tmp_path, capsys):
    """Tracker reports no change; CLI prints 'no changes'."""
    cmd = ["/bin/sh", "-c", "run.sh"]
    old_l = _layer(cmd)
    new_l = _layer(cmd)
    report = diff_cmd(old_l, new_l)
    assert not report.has_changes

    old_f = _write(tmp_path, "o.json", cmd)
    new_f = _write(tmp_path, "n.json", cmd)
    cmd_cmd_diff(_Args(old_f, new_f))
    out = capsys.readouterr().out
    assert "no changes" in out


def test_roundtrip_modification(tmp_path, capsys):
    """Tracker detects modification; CLI JSON reflects both sides."""
    old_cmd = ["/bin/sh", "-c", "v1"]
    new_cmd = ["/bin/sh", "-c", "v2"]

    old_l = _layer(old_cmd)
    new_l = _layer(new_cmd)
    report = diff_cmd(old_l, new_l)
    assert report.has_changes
    assert report.delta.is_modified

    old_f = _write(tmp_path, "o.json", old_cmd)
    new_f = _write(tmp_path, "n.json", new_cmd)
    cmd_cmd_diff(_Args(old_f, new_f, fmt="json"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["has_changes"] is True
    assert payload["old"] == old_cmd
    assert payload["new"] == new_cmd


def test_roundtrip_addition(tmp_path, capsys):
    """No CMD -> CMD detected as addition."""
    old_f = _write(tmp_path, "o.json", None)
    new_f = _write(tmp_path, "n.json", ["/app", "serve"])
    cmd_cmd_diff(_Args(old_f, new_f, fmt="json"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["has_changes"] is True
    assert payload["old"] is None
    assert payload["new"] == ["/app", "serve"]
