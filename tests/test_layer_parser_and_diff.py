"""Tests for layer_parser and diff_engine modules."""

import json
import pytest

from deploy_diff.layer_parser import LayerInfo, parse_image_config
from deploy_diff.diff_engine import ChangeKind, diff_layers, summary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG = {
    "history": [
        {"created_by": "/bin/sh -c #(nop) FROM scratch", "empty_layer": True},
        {"created_by": "/bin/sh -c apt-get install -y curl"},
        {"created_by": "/bin/sh -c apt-get install -y vim"},
    ],
    "rootfs": {
        "diff_ids": [
            "sha256:aaa111aaa111aaa111aaa111aaa111aa",
            "sha256:bbb222bbb222bbb222bbb222bbb222bb",
        ]
    },
}

TARGET_CONFIG = {
    "history": [
        {"created_by": "/bin/sh -c #(nop) FROM scratch", "empty_layer": True},
        {"created_by": "/bin/sh -c apt-get install -y curl"},
        {"created_by": "/bin/sh -c apt-get install -y git"},
    ],
    "rootfs": {
        "diff_ids": [
            "sha256:aaa111aaa111aaa111aaa111aaa111aa",
            "sha256:ccc333ccc333ccc333ccc333ccc333cc",
        ]
    },
}


# ---------------------------------------------------------------------------
# parse_image_config tests
# ---------------------------------------------------------------------------

class TestParseImageConfig:
    def test_returns_correct_count(self):
        layers = parse_image_config(BASE_CONFIG)
        # 1 empty + 2 real
        assert len(layers) == 3

    def test_empty_layer_flagged(self):
        layers = parse_image_config(BASE_CONFIG)
        assert layers[0].empty is True

    def test_real_layers_have_digests(self):
        layers = parse_image_config(BASE_CONFIG)
        real = [l for l in layers if not l.empty]
        assert real[0].digest == "sha256:aaa111aaa111aaa111aaa111aaa111aa"

    def test_accepts_json_string(self):
        layers = parse_image_config(json.dumps(BASE_CONFIG))
        assert len(layers) == 3

    def test_short_digest(self):
        layer = LayerInfo(digest="sha256:abcdef123456789")
        assert layer.short_digest == "abcdef123456"


# ---------------------------------------------------------------------------
# diff_layers tests
# ---------------------------------------------------------------------------

class TestDiffLayers:
    def setup_method(self):
        self.base = parse_image_config(BASE_CONFIG)
        self.target = parse_image_config(TARGET_CONFIG)

    def test_unchanged_layer_detected(self):
        changes = diff_layers(self.base, self.target)
        unchanged = [c for c in changes if c.kind == ChangeKind.UNCHANGED]
        assert len(unchanged) == 1
        assert unchanged[0].layer.digest == "sha256:aaa111aaa111aaa111aaa111aaa111aa"

    def test_removed_layer_detected(self):
        changes = diff_layers(self.base, self.target)
        removed = [c for c in changes if c.kind == ChangeKind.REMOVED]
        assert len(removed) == 1
        assert "vim" in removed[0].layer.created_by

    def test_added_layer_detected(self):
        changes = diff_layers(self.base, self.target)
        added = [c for c in changes if c.kind == ChangeKind.ADDED]
        assert len(added) == 1
        assert "git" in added[0].layer.created_by

    def test_summary_counts(self):
        changes = diff_layers(self.base, self.target)
        s = summary(changes)
        assert s["added"] == 1
        assert s["removed"] == 1
        assert s["unchanged"] == 1

    def test_identical_images_no_changes(self):
        changes = diff_layers(self.base, self.base)
        s = summary(changes)
        assert s["added"] == 0
        assert s["removed"] == 0
