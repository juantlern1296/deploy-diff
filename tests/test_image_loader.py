"""Tests for deploy_diff.image_loader."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from deploy_diff.image_loader import (
    ImageLoadError,
    ImageManifest,
    load_image,
    load_image_from_file,
)

_FAKE_CONFIG: dict = {
    "Id": "sha256:abc123",
    "RepoTags": ["myapp:latest"],
    "RootFS": {"Layers": []},
}


def _mock_run(stdout: str):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = 0
    return mock


class TestLoadImage:
    def test_returns_manifest_instance(self):
        raw = json.dumps(_FAKE_CONFIG)
        with patch("subprocess.run", return_value=_mock_run(raw)):
            manifest = load_image("myapp:latest")
        assert isinstance(manifest, ImageManifest)

    def test_reference_stored(self):
        raw = json.dumps(_FAKE_CONFIG)
        with patch("subprocess.run", return_value=_mock_run(raw)):
            manifest = load_image("myapp:latest")
        assert manifest.reference == "myapp:latest"

    def test_image_id_from_config(self):
        raw = json.dumps(_FAKE_CONFIG)
        with patch("subprocess.run", return_value=_mock_run(raw)):
            manifest = load_image("myapp:latest")
        assert manifest.image_id == "sha256:abc123"

    def test_image_id_falls_back_to_reference(self):
        config = {"RootFS": {"Layers": []}}
        raw = json.dumps(config)
        with patch("subprocess.run", return_value=_mock_run(raw)):
            manifest = load_image("fallback:tag")
        assert manifest.image_id == "fallback:tag"

    def test_list_wrapped_output_parsed(self):
        raw = json.dumps([_FAKE_CONFIG])
        with patch("subprocess.run", return_value=_mock_run(raw)):
            manifest = load_image("myapp:latest")
        assert manifest.config["Id"] == "sha256:abc123"

    def test_raises_on_empty_list(self):
        raw = json.dumps([])
        with patch("subprocess.run", return_value=_mock_run(raw)):
            with pytest.raises(ImageLoadError, match="No data returned"):
                load_image("myapp:latest")

    def test_raises_on_subprocess_error(self):
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "docker", stderr="not found"),
        ):
            with pytest.raises(ImageLoadError, match="docker inspect failed"):
                load_image("bad:image")

    def test_raises_when_docker_missing(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(ImageLoadError, match="docker executable not found"):
                load_image("any:image")

    def test_raises_on_invalid_json(self):
        with patch("subprocess.run", return_value=_mock_run("not-json")):
            with pytest.raises(ImageLoadError, match="Failed to parse"):
                load_image("myapp:latest")


class TestLoadImageFromFile:
    def test_loads_json_file(self, tmp_path):
        p = tmp_path / "image.json"
        p.write_text(json.dumps(_FAKE_CONFIG))
        manifest = load_image_from_file(str(p))
        assert manifest.reference == "myapp:latest"

    def test_raises_on_missing_file(self):
        with pytest.raises(ImageLoadError, match="Failed to load image file"):
            load_image_from_file("/nonexistent/path.json")

    def test_raises_on_bad_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{{invalid")
        with pytest.raises(ImageLoadError, match="Failed to load image file"):
            load_image_from_file(str(p))
