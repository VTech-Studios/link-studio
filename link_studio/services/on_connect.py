"""The headless `--apply` path run by the systemd unit when the camera connects."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from ..domain import CameraError
from ..ports import CameraLocator
from .startup import StartupService


@dataclass(frozen=True)
class Timing:
    """How long to wait for the camera, and how long to let it settle.

    The systemd trigger is the camera's sound card, which can appear before
    the video node does, hence the wait. The firmware keeps initialising
    for a moment after the node appears and overwrites anything sent too
    early with its own defaults, hence the settle delay.
    """

    wait_seconds: float = 15.0
    poll_seconds: float = 0.5
    settle_seconds: float = 2.0


DEFAULT_TIMING = Timing()


class ApplyOnConnect:
    """Waits for the camera, then applies the saved profile."""

    def __init__(
        self,
        locator: CameraLocator,
        service_for: Callable[[str], StartupService],
        report: Callable[[str], None],
        *,
        timing: Timing = DEFAULT_TIMING,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._locator = locator
        self._service_for = service_for
        self._report = report
        self._timing = timing
        self._sleep = sleep
        self._clock = clock

    def run(self) -> int:
        """Apply the profile and return a process exit status, 0 when every setting applied."""
        device = self._wait_for_camera()
        if device is None:
            self._report("link-studio: the camera did not appear")
            return 1

        self._sleep(self._timing.settle_seconds)
        try:
            failures = self._service_for(device).apply_saved()
        except CameraError as error:
            self._report(f"link-studio: {error}")
            return 1

        if failures:
            self._report(f"link-studio: could not apply: {', '.join(failures)}")
            return 1
        self._report(f"link-studio: startup settings applied to {device}")
        return 0

    def _wait_for_camera(self) -> str | None:
        deadline = self._clock() + self._timing.wait_seconds
        while (device := self._locator.find()) is None and self._clock() < deadline:
            self._sleep(self._timing.poll_seconds)
        return device
