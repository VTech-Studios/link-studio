from pathlib import Path

import pytest

from link_studio.domain import CameraError, RotationDirection
from link_studio.infrastructure.rotation import START_TIMEOUT_SECONDS, CamRotateService
from tests.fakes import FakeRunner


def test_start_passes_direction_with_a_longer_timeout(tmp_path: Path) -> None:
    loopback = tmp_path / "video10"
    loopback.touch()
    runner = FakeRunner()

    CamRotateService(runner, loopback).start(RotationDirection.ANTICLOCKWISE)

    assert runner.calls == [["cam-rotate", "start", "ccw"]]
    assert runner.timeouts == [START_TIMEOUT_SECONDS]


def test_start_without_loopback_explains_the_sudo_step(tmp_path: Path) -> None:
    runner = FakeRunner()

    with pytest.raises(CameraError, match="in a terminal once per boot"):
        CamRotateService(runner, tmp_path / "video10").start(RotationDirection.CLOCKWISE)
    assert runner.calls == []


def test_stop(tmp_path: Path) -> None:
    runner = FakeRunner()

    CamRotateService(runner, tmp_path).stop()

    assert runner.calls == [["cam-rotate", "stop"]]


@pytest.mark.parametrize(
    ("response", "running"),
    [
        ("Running (pid 42), output /dev/video10\n", True),
        ("Not running\n", False),
        (CameraError("cam-rotate is not installed"), False),
    ],
)
def test_is_running(tmp_path: Path, response: str | Exception, running: bool) -> None:
    runner = FakeRunner([(["cam-rotate", "status"], response)])

    assert CamRotateService(runner, tmp_path).is_running() is running
