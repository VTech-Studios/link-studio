from collections.abc import Callable

import pytest

from link_studio.domain import CameraError, CameraMode, TrackingFrame
from link_studio.infrastructure.linkctl import LinkctlBackend
from tests.fakes import FakeRunner

CONFIRMED = "Connected: Insta360 Link 2 (/dev/video0)\nOK\n"


def backend(output: str = CONFIRMED) -> tuple[LinkctlBackend, FakeRunner]:
    runner = FakeRunner([(["linkctl"], output)])
    return LinkctlBackend(runner, "/dev/video0"), runner


@pytest.mark.parametrize(
    ("action", "arguments"),
    [
        (lambda b: b.set_tracking(True), ["tracking", "on"]),
        (lambda b: b.set_tracking(False), ["tracking", "off"]),
        (lambda b: b.set_framing(TrackingFrame.HALF_BODY), ["frame", "half"]),
        (lambda b: b.set_mode(CameraMode.NORMAL), ["normal"]),
        (lambda b: b.set_mode(CameraMode.DESKVIEW), ["deskview", "on"]),
        (lambda b: b.set_mode(CameraMode.OVERHEAD), ["overhead", "on"]),
        (lambda b: b.centre(), ["home"]),
        (lambda b: b.save_preset(0), ["preset", "save", "0"]),
        (lambda b: b.recall_preset(5), ["preset", "recall", "5"]),
    ],
)
def test_commands(action: Callable[[LinkctlBackend], None], arguments: list[str]) -> None:
    linkctl, runner = backend()

    action(linkctl)

    assert runner.calls == [["linkctl", "-d", "/dev/video0", *arguments]]


def test_missing_ok_is_a_failure_even_with_exit_status_zero() -> None:
    linkctl, _ = backend("Connected\nCommand may have failed. Try running with -v for details.\n")

    with pytest.raises(CameraError, match="did not confirm 'linkctl tracking off'"):
        linkctl.set_tracking(False)


@pytest.mark.parametrize("slot", [-1, 6])
def test_rejects_preset_slots_outside_the_camera_range(slot: int) -> None:
    linkctl, runner = backend()

    with pytest.raises(CameraError, match="0 to 5"):
        linkctl.save_preset(slot)
    assert runner.calls == []
