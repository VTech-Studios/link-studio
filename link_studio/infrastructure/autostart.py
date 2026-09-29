"""Re-applies the profile on connect through a systemd user service.

The camera forgets its settings on power loss and returns with AI tracking
on. Its defaults can only be changed from the vendor's Windows and macOS
app, so instead the saved profile is re-applied whenever the camera appears.

No root access is needed. The camera contains a microphone, systemd creates
a device unit for every sound card, and a user service that is `WantedBy`
that device unit is started by the user's own session whenever the camera
connects. Video nodes are not tagged for systemd, which is why the sound
card is the trigger.
"""

from __future__ import annotations

from pathlib import Path

from ..domain import CameraError
from ..ports import CommandRunner

UNIT_NAME = "link-studio-apply.service"


class SystemdAutostart:
    """Autostart implemented as a oneshot systemd user unit."""

    def __init__(self, runner: CommandRunner, unit_dir: Path, camera_name: str, apply_command: str) -> None:
        self._runner = runner
        self._unit_path = unit_dir / UNIT_NAME
        self._camera_name = camera_name
        self._apply_command = apply_command

    def is_enabled(self) -> bool:
        """Report whether the unit is enabled.

        `systemctl is-enabled` exits non-zero for disabled and missing units
        alike, so any failure means not enabled.
        """
        try:
            return self._systemctl("is-enabled", UNIT_NAME).strip() == "enabled"
        except CameraError:
            return False

    def enable(self) -> None:
        device_unit = self._camera_device_unit()
        self._unit_path.parent.mkdir(parents=True, exist_ok=True)
        self._unit_path.write_text(self.render_unit(device_unit))
        self._systemctl("daemon-reload")
        self._systemctl("enable", UNIT_NAME)

    def disable(self) -> None:
        self._systemctl("disable", UNIT_NAME)

    def render_unit(self, device_unit: str) -> str:
        return (
            "# Written by Link Studio: re-applies saved camera settings on connect.\n"
            "[Unit]\n"
            f"Description=Apply Link Studio startup settings to the {self._camera_name} camera\n"
            f"After={device_unit}\n"
            "\n"
            "[Service]\n"
            "Type=oneshot\n"
            f"ExecStart={self._apply_command}\n"
            "\n"
            "[Install]\n"
            f"WantedBy={device_unit}\n"
        )

    def _camera_device_unit(self) -> str:
        """Find the camera's sound card device unit.

        The by-id name is used because it stays the same when the camera is
        plugged into a different port.
        """
        listing = self._systemctl("list-units", "--type=device", "--all", "--plain", "--no-legend")
        for line in listing.splitlines():
            unit = line.split(maxsplit=1)[0] if line.strip() else ""
            if "by\\x2did" in unit and self._camera_name in unit:
                return unit
        raise CameraError("The camera is not connected. Plug it in, then enable automatic apply.")

    def _systemctl(self, *args: str) -> str:
        return self._runner.run(["systemctl", "--user", *args])
