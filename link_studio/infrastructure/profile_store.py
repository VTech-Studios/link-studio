"""Persists the startup profile as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from ..domain import CameraError, Profile


class JsonProfileStore:
    """ProfileStore backed by a single JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def location(self) -> str:
        return str(self._path)

    def load(self) -> Profile | None:
        try:
            text = self._path.read_text()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise CameraError(f"Could not read {self._path}: {error}") from error
        try:
            return Profile.from_dict(json.loads(text))
        except json.JSONDecodeError as error:
            raise CameraError(f"{self._path} is not valid JSON: {error}") from error

    def save(self, profile: Profile) -> None:
        """Write to a temporary file, then rename over the old one.

        The rename is atomic, so a crash or power cut mid-write can never
        leave a truncated profile for the next camera connect to fail on.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(profile.to_dict(), indent=2) + "\n")
        temporary.replace(self._path)
