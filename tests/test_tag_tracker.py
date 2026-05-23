"""Tests for deploy_diff.tag_tracker."""

import pytest

from deploy_diff.tag_tracker import (
    TagDelta,
    TagReport,
    TagTrackerError,
    compare_tags,
)


# ---------------------------------------------------------------------------
# TagDelta.__str__
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = TagDelta(reference="myapp", old_tag=None, new_tag="v2")
    assert str(d) == "myapp: (none) -> v2"


def test_delta_str_removed():
    d = TagDelta(reference="myapp", old_tag="v1", new_tag=None)
    assert str(d) == "myapp: v1 -> (removed)"


def test_delta_str_modified():
    d = TagDelta(reference="myapp", old_tag="v1", new_tag="v2")
    assert str(d) == "myapp: v1 -> v2"


# ---------------------------------------------------------------------------
# TagDelta.is_promotion
# ---------------------------------------------------------------------------

def test_is_promotion_true_when_tags_differ():
    d = TagDelta(reference="svc", old_tag="v1", new_tag="v2")
    assert d.is_promotion is True


def test_is_promotion_false_when_old_tag_none():
    d = TagDelta(reference="svc", old_tag=None, new_tag="v2")
    assert d.is_promotion is False


def test_is_promotion_false_when_new_tag_none():
    d = TagDelta(reference="svc", old_tag="v1", new_tag=None)
    assert d.is_promotion is False


# ---------------------------------------------------------------------------
# TagReport
# ---------------------------------------------------------------------------

def test_report_total():
    deltas = [
        TagDelta("a", "v1", "v2"),
        TagDelta("b", None, "v1"),
    ]
    report = TagReport(deltas=deltas)
    assert report.total == 2


def test_report_promotions_only_includes_real_changes():
    deltas = [
        TagDelta("a", "v1", "v2"),   # promotion
        TagDelta("b", None, "v1"),   # not a promotion
    ]
    report = TagReport(deltas=deltas)
    assert len(report.promotions) == 1
    assert report.promotions[0].reference == "a"


def test_report_summary_no_changes():
    report = TagReport()
    assert report.summary() == "No tag changes detected."


def test_report_summary_lists_all_deltas():
    deltas = [TagDelta("svc", "v1", "v2")]
    report = TagReport(deltas=deltas)
    assert "svc" in report.summary()


# ---------------------------------------------------------------------------
# compare_tags
# ---------------------------------------------------------------------------

def test_compare_no_changes():
    report = compare_tags({"app": "v1"}, {"app": "v1"})
    assert report.total == 0


def test_compare_detects_update():
    report = compare_tags({"app": "v1"}, {"app": "v2"})
    assert report.total == 1
    assert report.deltas[0].old_tag == "v1"
    assert report.deltas[0].new_tag == "v2"


def test_compare_detects_new_reference():
    report = compare_tags({}, {"app": "v1"})
    assert report.total == 1
    assert report.deltas[0].old_tag is None


def test_compare_detects_removed_reference():
    report = compare_tags({"app": "v1"}, {})
    assert report.total == 1
    assert report.deltas[0].new_tag is None


def test_compare_raises_on_invalid_input():
    with pytest.raises(TagTrackerError):
        compare_tags("not-a-dict", {})  # type: ignore


def test_compare_results_sorted_by_reference():
    before = {"zebra": "v1", "alpha": "v1"}
    after = {"zebra": "v2", "alpha": "v2"}
    report = compare_tags(before, after)
    refs = [d.reference for d in report.deltas]
    assert refs == sorted(refs)
