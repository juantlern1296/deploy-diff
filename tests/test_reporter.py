"""Tests for deploy_diff.reporter."""

import json
from unittest.mock import patch

import pytest

from deploy_diff.diff_engine import ChangeKind, LayerChange
from deploy_diff.reporter import Report, ReportMeta, ReportSummary, build_report


def _make_change(
    kind: ChangeKind,
    digest: str = "abc123",
    command: str = "RUN echo hi",
    size_bytes: int = 512,
    empty: bool = False,
) -> LayerChange:
    return LayerChange(
        kind=kind,
        digest=digest,
        command=command,
        size_bytes=size_bytes,
        empty=empty,
    )


class TestBuildReport:
    def test_returns_report_instance(self):
        report = build_report([])
        assert isinstance(report, Report)

    def test_summary_counts_added(self):
        changes = [_make_change(ChangeKind.ADDED), _make_change(ChangeKind.ADDED)]
        report = build_report(changes)
        assert report.summary.added == 2
        assert report.summary.total == 2

    def test_summary_counts_removed(self):
        changes = [_make_change(ChangeKind.REMOVED)]
        report = build_report(changes)
        assert report.summary.removed == 1

    def test_summary_counts_modified(self):
        changes = [_make_change(ChangeKind.MODIFIED)]
        report = build_report(changes)
        assert report.summary.modified == 1

    def test_summary_counts_unchanged(self):
        changes = [_make_change(ChangeKind.UNCHANGED)]
        report = build_report(changes)
        assert report.summary.unchanged == 1

    def test_meta_images_stored(self):
        report = build_report([], base_image="img:v1", target_image="img:v2")
        assert report.meta.base_image == "img:v1"
        assert report.meta.target_image == "img:v2"

    def test_meta_generated_at_is_iso(self):
        report = build_report([])
        # Should not raise
        from datetime import datetime
        datetime.fromisoformat(report.meta.generated_at)

    def test_changes_list_length(self):
        changes = [_make_change(ChangeKind.ADDED), _make_change(ChangeKind.REMOVED)]
        report = build_report(changes)
        assert len(report.changes) == 2

    def test_change_dict_keys(self):
        changes = [_make_change(ChangeKind.ADDED, digest="deadbeef")]
        report = build_report(changes)
        keys = set(report.changes[0].keys())
        assert keys == {"kind", "digest", "command", "size_bytes", "empty"}

    def test_change_kind_is_string_value(self):
        changes = [_make_change(ChangeKind.ADDED)]
        report = build_report(changes)
        assert report.changes[0]["kind"] == ChangeKind.ADDED.value

    def test_text_is_string(self):
        report = build_report([_make_change(ChangeKind.ADDED)])
        assert isinstance(report.text, str)
        assert len(report.text) > 0


class TestReportToJson:
    def test_to_json_is_valid_json(self):
        report = build_report([_make_change(ChangeKind.ADDED)])
        parsed = json.loads(report.to_json())
        assert "meta" in parsed
        assert "summary" in parsed
        assert "changes" in parsed

    def test_to_json_summary_values(self):
        changes = [_make_change(ChangeKind.ADDED), _make_change(ChangeKind.REMOVED)]
        report = build_report(changes)
        parsed = json.loads(report.to_json())
        assert parsed["summary"]["added"] == 1
        assert parsed["summary"]["removed"] == 1
        assert parsed["summary"]["total"] == 2

    def test_to_json_custom_indent(self):
        report = build_report([])
        compact = report.to_json(indent=0)
        assert "\n" not in compact
