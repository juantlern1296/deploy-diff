"""Tests for deploy_diff.audit and deploy_diff.audit_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deploy_diff.audit import (
    AuditEntry,
    AuditError,
    load_entries,
    make_entry,
    record,
)


@pytest.fixture()
def tmp_audit(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def _entry(**kwargs) -> AuditEntry:
    defaults = dict(
        reference_a="img:v1",
        reference_b="img:v2",
        added=2,
        removed=1,
        modified=3,
        output_format="text",
    )
    defaults.update(kwargs)
    return make_entry(**defaults)


# --- make_entry ---

def test_make_entry_returns_audit_entry():
    e = _entry()
    assert isinstance(e, AuditEntry)


def test_make_entry_stores_references():
    e = _entry(reference_a="a:1", reference_b="b:2")
    assert e.reference_a == "a:1"
    assert e.reference_b == "b:2"


def test_make_entry_counts():
    e = _entry(added=5, removed=3, modified=1)
    assert e.added == 5
    assert e.removed == 3
    assert e.modified == 1


def test_make_entry_default_tags_empty():
    e = _entry()
    assert e.tags == []


def test_make_entry_tags_stored():
    e = _entry(tags=["prod", "hotfix"])
    assert "prod" in e.tags


def test_make_entry_has_timestamp():
    e = _entry()
    assert "T" in e.timestamp  # ISO format


# --- record / load_entries ---

def test_record_creates_file(tmp_audit: Path):
    e = _entry()
    path = record(e, audit_dir=tmp_audit)
    assert path.exists()


def test_record_writes_valid_json(tmp_audit: Path):
    e = _entry()
    path = record(e, audit_dir=tmp_audit)
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["reference_a"] == "img:v1"


def test_record_appends_multiple(tmp_audit: Path):
    record(_entry(), audit_dir=tmp_audit)
    record(_entry(reference_a="x:1"), audit_dir=tmp_audit)
    entries = load_entries(tmp_audit)
    assert len(entries) == 2


def test_load_entries_empty_dir(tmp_audit: Path):
    entries = load_entries(tmp_audit)
    assert entries == []


def test_load_entries_returns_audit_entry_instances(tmp_audit: Path):
    record(_entry(), audit_dir=tmp_audit)
    entries = load_entries(tmp_audit)
    assert all(isinstance(e, AuditEntry) for e in entries)


def test_record_raises_audit_error_on_bad_path():
    bad_dir = Path("/proc/nonexistent_deploy_diff_test")
    with pytest.raises(AuditError):
        record(_entry(), audit_dir=bad_dir)
