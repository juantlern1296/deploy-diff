"""Tests for deploy_diff.baseline."""

from __future__ import annotations

import pytest
from pathlib import Path

from deploy_diff.baseline import (
    Baseline,
    BaselineError,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from deploy_diff.snapshot import Snapshot


def _fake_snapshot(ref: str = "myimage:latest") -> Snapshot:
    return Snapshot(
        reference=ref,
        image_id="sha256:abc123",
        layers=["sha256:layer1", "sha256:layer2"],
    )


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path / "baselines"


def test_save_creates_file(tmp_base):
    snap = _fake_snapshot()
    path = save_baseline("prod", snap, base_dir=tmp_base)
    assert path.exists()


def test_save_returns_correct_path(tmp_base):
    snap = _fake_snapshot()
    path = save_baseline("staging", snap, base_dir=tmp_base)
    assert path.name == "staging.json"


def test_load_returns_baseline_instance(tmp_base):
    snap = _fake_snapshot()
    save_baseline("prod", snap, base_dir=tmp_base)
    bl = load_baseline("prod", base_dir=tmp_base)
    assert isinstance(bl, Baseline)


def test_load_preserves_reference(tmp_base):
    snap = _fake_snapshot(ref="registry/app:v2")
    save_baseline("app", snap, base_dir=tmp_base)
    bl = load_baseline("app", base_dir=tmp_base)
    assert bl.reference == "registry/app:v2"


def test_load_preserves_layers(tmp_base):
    snap = _fake_snapshot()
    save_baseline("prod", snap, base_dir=tmp_base)
    bl = load_baseline("prod", base_dir=tmp_base)
    assert bl.layers == ["sha256:layer1", "sha256:layer2"]


def test_load_missing_raises(tmp_base):
    with pytest.raises(BaselineError, match="No baseline found"):
        load_baseline("ghost", base_dir=tmp_base)


def test_to_snapshot_returns_snapshot(tmp_base):
    snap = _fake_snapshot()
    save_baseline("prod", snap, base_dir=tmp_base)
    bl = load_baseline("prod", base_dir=tmp_base)
    recovered = bl.to_snapshot()
    assert isinstance(recovered, Snapshot)
    assert recovered.image_id == snap.image_id


def test_list_empty_when_no_dir(tmp_base):
    assert list_baselines(base_dir=tmp_base) == []


def test_list_returns_saved_names(tmp_base):
    save_baseline("alpha", _fake_snapshot(), base_dir=tmp_base)
    save_baseline("beta", _fake_snapshot(), base_dir=tmp_base)
    names = list_baselines(base_dir=tmp_base)
    assert "alpha" in names
    assert "beta" in names


def test_delete_removes_file(tmp_base):
    save_baseline("old", _fake_snapshot(), base_dir=tmp_base)
    result = delete_baseline("old", base_dir=tmp_base)
    assert result is True
    assert list_baselines(base_dir=tmp_base) == []


def test_delete_nonexistent_returns_false(tmp_base):
    result = delete_baseline("nope", base_dir=tmp_base)
    assert result is False
