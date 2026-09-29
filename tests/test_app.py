import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from link_studio import app
from link_studio.config import Config
from link_studio.infrastructure.linkctl import LinkctlBackend
from link_studio.infrastructure.v4l2 import V4l2ControlBackend
from link_studio.ports import CommandRunner
from link_studio.services.on_connect import Timing
from link_studio.wiring import build_services
from tests.fakes import FakeRunner


@pytest.fixture
def config(tmp_path: Path) -> Config:
    base = Config.from_environment({"HOME": str(tmp_path)}, python="/usr/bin/python3")
    return replace(base, sysfs_video=tmp_path / "sysfs", loopback_device=tmp_path / "video10")


def add_camera(config: Config) -> None:
    node = config.sysfs_video / "video0"
    node.mkdir(parents=True)
    (node / "name").write_text("Insta360 Link 2\n")
    (node / "index").write_text("0\n")


def test_build_services_wires_one_device(config: Config) -> None:
    services = build_services(config, "/dev/video0", FakeRunner())

    assert isinstance(services.controls, V4l2ControlBackend)
    assert isinstance(services.vendor, LinkctlBackend)
    assert services.startup.location == str(config.profile_path)


def test_run_apply_applies_the_saved_profile_end_to_end(config: Config) -> None:
    add_camera(config)
    config.profile_path.parent.mkdir(parents=True)
    config.profile_path.write_text(
        json.dumps({"tracking": False, "mode": "normal", "controls": {"zoom_absolute": 120}})
    )
    runner = FakeRunner([(["linkctl"], "OK\n")])

    assert app.run_apply(config, runner, Timing(wait_seconds=0, settle_seconds=0)) == 0
    assert runner.calls == [
        ["linkctl", "-d", "/dev/video0", "normal"],
        ["v4l2-ctl", "-d", "/dev/video0", "-c", "zoom_absolute=120"],
    ]


def test_main_dispatches_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def recorder(name: str) -> Callable[[Config, CommandRunner], int]:
        def run(_config: Config, _runner: CommandRunner) -> int:
            calls.append(name)
            return 0

        return run

    monkeypatch.setattr(app, "run_apply", recorder("apply"))
    monkeypatch.setattr(app, "run_gui", recorder("gui"))

    assert app.main(["--apply"]) == 0
    assert app.main([]) == 0
    assert calls == ["apply", "gui"]


def test_apply_path_does_not_import_qt() -> None:
    script = "import sys, link_studio.app; print(any(m.startswith('PySide6') for m in sys.modules))"

    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)

    assert result.stdout.strip() == "False"
