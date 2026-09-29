from pathlib import Path

import pytest

from link_studio.domain import CameraError
from link_studio.infrastructure.autostart import UNIT_NAME, SystemdAutostart
from tests.fakes import FakeRunner

DEVICE_UNIT = r"dev-snd-by\x2did-usb\x2dInsta360_Insta360_Link_2\x2d02.device"
DEVICE_LISTING = (
    r"dev-snd-controlC5.device loaded active plugged Insta360_Link_2"
    + "\n"
    + DEVICE_UNIT
    + " loaded active plugged Insta360_Link_2\n"
    + r"dev-snd-by\x2did-usb\x2dFocusrite_Scarlett.device loaded active plugged Scarlett"
    + "\n"
)
LIST_UNITS = ["systemctl", "--user", "list-units"]
APPLY = "/usr/bin/python3 -m link_studio --apply"


def autostart(tmp_path: Path, runner: FakeRunner) -> SystemdAutostart:
    return SystemdAutostart(runner, tmp_path / "systemd" / "user", "Insta360", APPLY)


def test_enable_writes_unit_bound_to_the_camera_and_enables_it(tmp_path: Path) -> None:
    runner = FakeRunner([(LIST_UNITS, DEVICE_LISTING)])

    autostart(tmp_path, runner).enable()

    unit = (tmp_path / "systemd" / "user" / UNIT_NAME).read_text()
    assert f"WantedBy={DEVICE_UNIT}\n" in unit
    assert f"After={DEVICE_UNIT}\n" in unit
    assert f"ExecStart={APPLY}\n" in unit
    assert "Type=oneshot\n" in unit
    assert runner.calls[1:] == [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", UNIT_NAME],
    ]


def test_enable_without_the_camera_writes_nothing(tmp_path: Path) -> None:
    runner = FakeRunner([(LIST_UNITS, "dev-sda.device loaded active plugged Disk\n")])

    with pytest.raises(CameraError, match="not connected"):
        autostart(tmp_path, runner).enable()
    assert not (tmp_path / "systemd").exists()


def test_disable(tmp_path: Path) -> None:
    runner = FakeRunner()

    autostart(tmp_path, runner).disable()

    assert runner.calls == [["systemctl", "--user", "disable", UNIT_NAME]]


@pytest.mark.parametrize(
    ("response", "expected"),
    [("enabled\n", True), ("disabled\n", False), (CameraError("No such unit"), False)],
)
def test_is_enabled(tmp_path: Path, response: str | Exception, expected: bool) -> None:
    runner = FakeRunner([(["systemctl", "--user", "is-enabled"], response)])

    assert autostart(tmp_path, runner).is_enabled() is expected
