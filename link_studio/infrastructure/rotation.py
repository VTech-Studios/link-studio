"""The `cam-rotate` script as a RotationService."""

from __future__ import annotations

from pathlib import Path

from ..domain import CameraError, RotationDirection
from ..ports import CommandRunner

START_TIMEOUT_SECONDS = 15.0


class CamRotateService:
    """RotationService that drives the `cam-rotate` script."""

    def __init__(self, runner: CommandRunner, loopback_device: Path) -> None:
        self._runner = runner
        self._loopback_device = loopback_device

    def is_running(self) -> bool:
        try:
            return self._runner.run(["cam-rotate", "status"]).startswith("Running")
        except CameraError:
            return False

    def start(self, direction: RotationDirection) -> None:
        """Start the rotated virtual camera.

        cam-rotate loads its kernel module with sudo, and a GUI has no
        terminal to answer the password prompt. Failing early with
        instructions is better than hanging on a prompt nobody can see.
        """
        if not self._loopback_device.exists():
            raise CameraError("Run 'cam-rotate start' in a terminal once per boot first. It needs sudo.")
        self._runner.run(["cam-rotate", "start", direction.value], timeout=START_TIMEOUT_SECONDS)

    def stop(self) -> None:
        self._runner.run(["cam-rotate", "stop"])
