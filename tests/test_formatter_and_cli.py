"""Tests for deploy_diff.formatter and deploy_diff.cli."""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from deploy_diff.diff_engine import ChangeKind, LayerChange
from deploy_diff.formatter import format_change, format_changelog
from deploy_diff.cli import main, build_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_change(kind: ChangeKind, digest="sha256:abcd1234", cmd="/bin/sh -c echo hi", empty=False):
    return LayerChange(kind=kind, digest=digest, created_by=cmd, empty=empty)


# ---------------------------------------------------------------------------
# format_change
# ---------------------------------------------------------------------------

class TestFormatChange:
    def test_added_symbol_plain(self):
        c = _make_change(ChangeKind.ADDED)
        line = format_change(c, color=False)
        assert line.startswith("+")

    def test_removed_symbol_plain(self):
        c = _make_change(ChangeKind.REMOVED)
        line = format_change(c, color=False)
        assert line.startswith("-")

    def test_modified_symbol_plain(self):
        c = _make_change(ChangeKind.MODIFIED)
        line = format_change(c, color=False)
        assert line.startswith("~")

    def test_digest_in_output(self):
        c = _make_change(ChangeKind.ADDED, digest="sha256:deadbeef")
        line = format_change(c, color=False)
        assert "deadbeef" in line

    def test_long_command_truncated(self):
        long_cmd = "x" * 100
        c = _make_change(ChangeKind.ADDED, cmd=long_cmd)
        line = format_change(c, color=False)
        assert "…" in line
        assert len(line) < 120

    def test_empty_digest_fallback(self):
        c = LayerChange(kind=ChangeKind.ADDED, digest=None, created_by="cmd", empty=True)
        line = format_change(c, color=False)
        assert "(empty)" in line


# ---------------------------------------------------------------------------
# format_changelog
# ---------------------------------------------------------------------------

class TestFormatChangelog:
    def test_header_contains_image_names(self):
        result = format_changelog([], image_from="img-a", image_to="img-b", color=False)
        assert "img-a" in result
        assert "img-b" in result

    def test_empty_changes_message(self):
        result = format_changelog([], color=False)
        assert "no layers" in result

    def test_summary_counts(self):
        changes = [
            _make_change(ChangeKind.ADDED),
            _make_change(ChangeKind.ADDED),
            _make_change(ChangeKind.REMOVED),
        ]
        result = format_changelog(changes, color=False)
        assert "2 added" in result
        assert "1 removed" in result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def _write_json(self, tmp_path, name, data):
        p = tmp_path / name
        p.write_text(json.dumps(data))
        return str(p)

    def _minimal_config(self, cmds):
        return {
            "rootfs": {"diff_ids": [f"sha256:{i:064x}" for i in range(len(cmds))]},
            "history": [{"created_by": c, "empty_layer": False} for c in cmds],
        }

    def test_plain_output_exit_zero(self, tmp_path):
        base = self._write_json(tmp_path, "base.json", self._minimal_config(["cmd1"]))
        target = self._write_json(tmp_path, "target.json", self._minimal_config(["cmd1", "cmd2"]))
        rc = main([base, target, "--no-color"])
        assert rc == 0

    def test_json_output_valid(self, tmp_path, capsys):
        base = self._write_json(tmp_path, "base.json", self._minimal_config(["cmd1"]))
        target = self._write_json(tmp_path, "target.json", self._minimal_config(["cmd1", "cmd2"]))
        rc = main([base, target, "--json"])
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)

    def test_missing_file_returns_error(self):
        rc = main(["nonexistent_base.json", "nonexistent_target.json"])
        assert rc == 1
