"""Insta360 vendor features through `linkctl`.

Tracking, modes and presets live in a vendor extension unit that `v4l2-ctl`
cannot address. `linkctl`, from
https://github.com/vrwallace/Insta360-Link-1-and-2-Controller-for-Linux,
already speaks that protocol, so it is wrapped here instead of
re-implementing its ioctls.
"""

from __future__ import annotations

from ..domain import PRESET_SLOTS, CameraError, CameraMode, TrackingFrame
from ..ports import CommandRunner


class LinkctlBackend:
    """TrackingBackend and GimbalBackend for one video device."""

    def __init__(self, runner: CommandRunner, device: str) -> None:
        self._runner = runner
        self._device = device

    def set_tracking(self, enabled: bool) -> None:
        self._command("tracking", "on" if enabled else "off")

    def set_framing(self, frame: TrackingFrame) -> None:
        self._command("frame", frame.value)

    def set_mode(self, mode: CameraMode) -> None:
        if mode is CameraMode.NORMAL:
            self._command("normal")
        else:
            self._command(mode.value, "on")

    def centre(self) -> None:
        self._command("home")

    def save_preset(self, slot: int) -> None:
        self._command("preset", "save", str(_checked_slot(slot)))

    def recall_preset(self, slot: int) -> None:
        self._command("preset", "recall", str(_checked_slot(slot)))

    def _command(self, *args: str) -> None:
        """Run linkctl and confirm success.

        linkctl exits with status 0 even when the camera rejects a command,
        and reports success only by printing "OK" as its last line.
        """
        output = self._runner.run(["linkctl", "-d", self._device, *args])
        if not output.rstrip().endswith("OK"):
            raise CameraError(f"The camera did not confirm 'linkctl {' '.join(args)}'")


def _checked_slot(slot: int) -> int:
    if slot not in PRESET_SLOTS:
        raise CameraError(f"Preset slot must be {PRESET_SLOTS.start} to {PRESET_SLOTS.stop - 1}")
    return slot
