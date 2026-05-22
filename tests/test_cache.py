"""Tests for deploy_diff.cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deploy_diff import cache


@pytest.fixture()
def tmp_cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


def test_cache_key_is_deterministic():
    key1 = cache._cache_key("nginx:latest")
    key2 = cache._cache_key("nginx:latest")
    assert key1 == key2


def test_cache_key_differs_for_different_refs():
    assert cache._cache_key("nginx:latest") != cache._cache_key("nginx:1.25")


def test_cache_key_ends_with_json():
    assert cache._cache_key("myapp:v1").endswith(".json")


def test_load_returns_none_when_missing(tmp_cache):
    result = cache.load("ghost:latest", cache_dir=tmp_cache)
    assert result is None


def test_save_creates_file(tmp_cache):
    path = cache.save("nginx:latest", {"layers": []}, cache_dir=tmp_cache)
    assert path.exists()


def test_save_and_load_roundtrip(tmp_cache):
    data = {"layers": ["sha256:abc", "sha256:def"], "count": 2}
    cache.save("myimage:v2", data, cache_dir=tmp_cache)
    loaded = cache.load("myimage:v2", cache_dir=tmp_cache)
    assert loaded == data


def test_load_returns_none_on_corrupt_file(tmp_cache):
    tmp_cache.mkdir(parents=True)
    path = cache.cache_path("bad:ref", cache_dir=tmp_cache)
    path.write_text("not valid json", encoding="utf-8")
    assert cache.load("bad:ref", cache_dir=tmp_cache) is None


def test_invalidate_removes_file(tmp_cache):
    cache.save("to-remove:1", ["x"], cache_dir=tmp_cache)
    removed = cache.invalidate("to-remove:1", cache_dir=tmp_cache)
    assert removed is True
    assert cache.load("to-remove:1", cache_dir=tmp_cache) is None


def test_invalidate_returns_false_when_not_present(tmp_cache):
    assert cache.invalidate("nonexistent:0", cache_dir=tmp_cache) is False


def test_clear_removes_all_entries(tmp_cache):
    cache.save("img:1", {}, cache_dir=tmp_cache)
    cache.save("img:2", {}, cache_dir=tmp_cache)
    cache.save("img:3", {}, cache_dir=tmp_cache)
    count = cache.clear(cache_dir=tmp_cache)
    assert count == 3
    assert list(tmp_cache.glob("*.json")) == []


def test_clear_on_missing_dir_returns_zero(tmp_cache):
    assert cache.clear(cache_dir=tmp_cache) == 0
