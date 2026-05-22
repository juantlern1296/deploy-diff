"""Tests for deploy_diff.snapshot."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from deploy_diff.snapshot import (
    Snapshot,
    SnapshotError,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def _fake_manifest(reference="myrepo/app:v1", image_id="sha256:abc123"):
    layer = SimpleNamespace(digest="sha256:deadbeef", is_empty=False)
    m = SimpleNamespace(reference=reference, image_id=image_id, layers=[layer])
    return m


@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path / "snapshots"


def test_from_manifest_sets_reference(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    assert snap.reference == "myrepo/app:v1"


def test_from_manifest_sets_image_id(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest(image_id="sha256:xyz"))
    assert snap.image_id == "sha256:xyz"


def test_from_manifest_layers_encoded(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    assert snap.layers == [{"digest": "sha256:deadbeef", "empty": False}]


def test_from_manifest_created_at_is_string(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    assert isinstance(snap.created_at, str) and "T" in snap.created_at


def test_save_creates_file(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    path = save_snapshot(snap, directory=tmp_dir)
    assert path.exists()


def test_save_returns_correct_path(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest(reference="repo/img:latest"))
    path = save_snapshot(snap, directory=tmp_dir)
    assert path.suffix == ".json"


def test_save_content_is_valid_json(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    path = save_snapshot(snap, directory=tmp_dir)
    data = json.loads(path.read_text())
    assert data["image_id"] == "sha256:abc123"


def test_load_returns_snapshot(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    save_snapshot(snap, directory=tmp_dir)
    loaded = load_snapshot("myrepo/app:v1", directory=tmp_dir)
    assert isinstance(loaded, Snapshot)


def test_load_roundtrip_reference(tmp_dir):
    snap = Snapshot.from_manifest(_fake_manifest())
    save_snapshot(snap, directory=tmp_dir)
    loaded = load_snapshot("myrepo/app:v1", directory=tmp_dir)
    assert loaded.reference == "myrepo/app:v1"


def test_load_missing_raises(tmp_dir):
    with pytest.raises(SnapshotError, match="No snapshot found"):
        load_snapshot("ghost/image:nope", directory=tmp_dir)


def test_list_snapshots_empty_dir(tmp_dir):
    assert list_snapshots(directory=tmp_dir) == []


def test_list_snapshots_returns_references(tmp_dir):
    for ref in ["org/a:1", "org/b:2"]:
        save_snapshot(Snapshot.from_manifest(_fake_manifest(reference=ref)), directory=tmp_dir)
    refs = list_snapshots(directory=tmp_dir)
    assert len(refs) == 2


def test_list_snapshots_nonexistent_dir(tmp_path):
    assert list_snapshots(directory=tmp_path / "nowhere") == []
