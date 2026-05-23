"""Tests for schema_validator and schema_cli."""

from __future__ import annotations

import json
import pytest

from deploy_diff.schema_validator import (
    ValidationError,
    ValidationResult,
    validate_report,
    assert_valid_report,
)


def _valid_doc() -> dict:
    return {
        "meta": {
            "generated_at": "2024-01-01T00:00:00",
            "image_a": "nginx:1.24",
            "image_b": "nginx:1.25",
        },
        "summary": {"added": 1, "removed": 0, "modified": 2, "total": 3},
        "changes": [{"kind": "added", "digest": "abc123"}],
    }


class TestValidationResult:
    def test_bool_true_when_valid(self):
        r = ValidationResult(True, [])
        assert bool(r) is True

    def test_bool_false_when_invalid(self):
        r = ValidationResult(False, ["missing key 'x'"])
        assert bool(r) is False

    def test_str_ok_when_valid(self):
        assert str(ValidationResult(True, [])) == "OK"

    def test_str_lists_errors(self):
        r = ValidationResult(False, ["err1", "err2"])
        assert "err1" in str(r)
        assert "err2" in str(r)


class TestValidateReport:
    def test_valid_doc_passes(self):
        assert validate_report(_valid_doc()).valid

    def test_non_dict_fails(self):
        result = validate_report(["not", "a", "dict"])
        assert not result
        assert any("mapping" in e for e in result.errors)

    def test_missing_top_level_key(self):
        doc = _valid_doc()
        del doc["changes"]
        result = validate_report(doc)
        assert not result
        assert any("changes" in e for e in result.errors)

    def test_missing_meta_key(self):
        doc = _valid_doc()
        del doc["meta"]["image_a"]
        result = validate_report(doc)
        assert not result
        assert any("image_a" in e for e in result.errors)

    def test_wrong_type_in_summary(self):
        doc = _valid_doc()
        doc["summary"]["added"] = "one"  # should be int
        result = validate_report(doc)
        assert not result
        assert any("added" in e for e in result.errors)

    def test_changes_not_list_fails(self):
        doc = _valid_doc()
        doc["changes"] = "not-a-list"
        result = validate_report(doc)
        assert not result

    def test_meta_not_dict_fails(self):
        doc = _valid_doc()
        doc["meta"] = "bad"
        result = validate_report(doc)
        assert not result


class TestAssertValidReport:
    def test_raises_on_invalid(self):
        with pytest.raises(ValidationError):
            assert_valid_report({"meta": {}, "summary": {}, "changes": "bad"})

    def test_passes_on_valid(self):
        assert_valid_report(_valid_doc())  # should not raise


class TestSchemaCli:
    def test_cmd_validate_valid_file(self, tmp_path):
        from deploy_diff.schema_cli import cmd_validate
        import argparse

        f = tmp_path / "report.json"
        f.write_text(json.dumps(_valid_doc()))
        args = argparse.Namespace(file=str(f), strict=False)
        assert cmd_validate(args) == 0

    def test_cmd_validate_missing_file(self, tmp_path):
        from deploy_diff.schema_cli import cmd_validate
        import argparse

        args = argparse.Namespace(file=str(tmp_path / "nope.json"), strict=False)
        assert cmd_validate(args) == 2

    def test_cmd_validate_invalid_json(self, tmp_path):
        from deploy_diff.schema_cli import cmd_validate
        import argparse

        f = tmp_path / "bad.json"
        f.write_text("{ not valid json ")
        args = argparse.Namespace(file=str(f), strict=False)
        assert cmd_validate(args) == 2

    def test_cmd_validate_invalid_doc(self, tmp_path):
        from deploy_diff.schema_cli import cmd_validate
        import argparse

        f = tmp_path / "invalid.json"
        f.write_text(json.dumps({"meta": {}, "summary": {}}))
        args = argparse.Namespace(file=str(f), strict=False)
        assert cmd_validate(args) == 1
