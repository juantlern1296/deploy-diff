"""Tests for deploy_diff.dependency_tracker."""

import pytest

from deploy_diff.diff_engine import ChangeKind, LayerChange
from deploy_diff.dependency_tracker import (
    DependencyReport,
    PackageDelta,
    track_dependencies,
)


def _change(path: str, kind: ChangeKind = ChangeKind.ADDED) -> LayerChange:
    return LayerChange(path=path, kind=kind, digest=None)


# ---------------------------------------------------------------------------
# PackageDelta.__str__
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = PackageDelta(name="requests", new_version="2.28.0", kind=ChangeKind.ADDED)
    assert str(d) == "+ requests 2.28.0"


def test_delta_str_removed():
    d = PackageDelta(name="flask", old_version="2.0.0", kind=ChangeKind.REMOVED)
    assert str(d) == "- flask 2.0.0"


def test_delta_str_modified():
    d = PackageDelta(name="numpy", old_version="1.23", new_version="1.24", kind=ChangeKind.MODIFIED)
    assert str(d) == "~ numpy 1.23 -> 1.24"


# ---------------------------------------------------------------------------
# track_dependencies — basic cases
# ---------------------------------------------------------------------------

def test_empty_changes_returns_empty_report():
    report = track_dependencies([])
    assert isinstance(report, DependencyReport)
    assert report.total == 0


def test_added_package_detected():
    changes = [
        _change("/usr/lib/python3/dist-packages/requests-2.28.0.dist-info/METADATA", ChangeKind.ADDED),
    ]
    report = track_dependencies(changes)
    assert len(report.added) == 1
    assert report.added[0].name == "requests"
    assert report.added[0].new_version == "2.28.0"


def test_removed_package_detected():
    changes = [
        _change("/usr/lib/python3/dist-packages/flask-2.0.0.dist-info/METADATA", ChangeKind.REMOVED),
    ]
    report = track_dependencies(changes)
    assert len(report.removed) == 1
    assert report.removed[0].name == "flask"


def test_upgraded_package_detected():
    changes = [
        _change("/usr/local/lib/python3.11/dist-packages/numpy-1.23.dist-info/METADATA", ChangeKind.REMOVED),
        _change("/usr/local/lib/python3.11/dist-packages/numpy-1.24.dist-info/METADATA", ChangeKind.ADDED),
    ]
    report = track_dependencies(changes)
    assert len(report.upgraded) == 1
    assert report.upgraded[0].old_version == "1.23"
    assert report.upgraded[0].new_version == "1.24"


def test_downgraded_package_detected():
    changes = [
        _change("/usr/lib/python3/dist-packages/boto3-1.30.0.dist-info/METADATA", ChangeKind.REMOVED),
        _change("/usr/lib/python3/dist-packages/boto3-1.20.0.dist-info/METADATA", ChangeKind.ADDED),
    ]
    report = track_dependencies(changes)
    assert len(report.downgraded) == 1


def test_non_package_paths_ignored():
    changes = [
        _change("/etc/nginx/nginx.conf", ChangeKind.ADDED),
        _change("/var/log/app.log", ChangeKind.REMOVED),
    ]
    report = track_dependencies(changes)
    assert report.total == 0


def test_total_counts_all_categories():
    changes = [
        _change("/usr/lib/python3/dist-packages/requests-2.28.0.dist-info/METADATA", ChangeKind.ADDED),
        _change("/usr/lib/python3/dist-packages/flask-2.0.0.dist-info/METADATA", ChangeKind.REMOVED),
    ]
    report = track_dependencies(changes)
    assert report.total == 2


def test_all_deltas_combines_lists():
    changes = [
        _change("/usr/lib/python3/dist-packages/requests-2.28.0.dist-info/METADATA", ChangeKind.ADDED),
        _change("/usr/lib/python3/dist-packages/flask-2.0.0.dist-info/METADATA", ChangeKind.REMOVED),
    ]
    report = track_dependencies(changes)
    names = {d.name for d in report.all_deltas()}
    assert "requests" in names
    assert "flask" in names
