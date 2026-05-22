"""Utilities for loading Docker image manifests and configs from a registry or local daemon."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class ImageManifest:
    """Holds raw manifest data and the resolved image reference."""

    reference: str
    config: dict[str, Any]
    raw: str

    @property
    def image_id(self) -> str:
        return self.config.get("Id", self.reference)


class ImageLoadError(RuntimeError):
    """Raised when an image cannot be inspected or parsed."""


def _run_docker_inspect(reference: str) -> str:
    """Run `docker inspect` and return raw JSON output."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{json .}}", reference],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise ImageLoadError(
            f"docker inspect failed for '{reference}': {exc.stderr.strip()}"
        ) from exc
    except FileNotFoundError as exc:
        raise ImageLoadError("docker executable not found on PATH") from exc


def load_image(reference: str) -> ImageManifest:
    """Load an image manifest from the local Docker daemon.

    Args:
        reference: An image name/tag or digest, e.g. ``nginx:latest``.

    Returns:
        A populated :class:`ImageManifest`.

    Raises:
        ImageLoadError: If the image cannot be found or the output cannot be parsed.
    """
    raw = _run_docker_inspect(reference)
    try:
        data = json.loads(raw)
        # `docker inspect` wraps the result in a list when called without --format
        # but with `{{json .}}` it returns a single object.
        if isinstance(data, list):
            if not data:
                raise ImageLoadError(f"No data returned for '{reference}'")
            data = data[0]
    except json.JSONDecodeError as exc:
        raise ImageLoadError(f"Failed to parse inspect output: {exc}") from exc

    return ImageManifest(reference=reference, config=data, raw=raw)


def load_image_from_file(path: str) -> ImageManifest:
    """Load an image manifest from a saved JSON file (e.g. docker save output)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        data = json.loads(raw)
        if isinstance(data, list):
            data = data[0]
        reference = data.get("RepoTags", [path])[0]
        return ImageManifest(reference=reference, config=data, raw=raw)
    except (OSError, json.JSONDecodeError, IndexError) as exc:
        raise ImageLoadError(f"Failed to load image file '{path}': {exc}") from exc
