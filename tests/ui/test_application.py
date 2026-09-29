import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox, QStatusBar, QWidget
from pytestqt.qtbot import QtBot

from link_studio import app
from link_studio.config import Config
from link_studio.domain import CameraError
from link_studio.infrastructure.linkctl import LinkctlBackend
from link_studio.services.startup import StartupService
from link_studio.ui import application
from link_studio.ui.controls_model import ControlsModel
from link_studio.ui.feedback import StatusFeedback
from link_studio.ui.main_window import MainWindow
from link_studio.wiring import Services
from tests.fakes import (
    FakeAutostart,
    FakeControlBackend,
    FakeRotation,
    FakeRunner,
    FakeTracking,
    MemoryProfileStore,
)
from tests.test_v4l2 import LINK_2_OUTPUT


@pytest.fixture
def config(tmp_path: Path) -> Config:
    base = Config.from_environment({"HOME": str(tmp_path)}, python=sys.executable)
    return replace(base, sysfs_video=tmp_path / "sysfs", loopback_device=tmp_path / "video10")


@pytest.fixture
def fatal_messages(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    messages: list[str] = []

    def critical(_parent: QWidget | None, _title: str, text: str) -> QMessageBox.StandardButton:
        messages.append(text)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "critical", critical)
    return messages


def add_camera(config: Config) -> None:
    node = config.sysfs_video / "video0"
    node.mkdir(parents=True)
    (node / "name").write_text("Insta360 Link 2\n")
    (node / "index").write_text("0\n")


def services(rotation: FakeRotation | None) -> Services:
    controls = FakeControlBackend()
    return Services(
        controls=controls,
        vendor=LinkctlBackend(FakeRunner(), "/dev/video0"),
        startup=StartupService(controls, FakeTracking(), MemoryProfileStore()),
        autostart=FakeAutostart(),
        rotation=rotation,
    )


@pytest.mark.parametrize(
    ("rotation", "titles"),
    [
        (FakeRotation(), ["Framing", "Image", "AI and modes", "Preview", "Rotated cam", "Startup"]),
        (None, ["Framing", "Image", "AI and modes", "Preview", "Startup"]),
    ],
)
def test_build_tabs_offers_rotation_only_when_available(
    qtbot: QtBot, config: Config, rotation: FakeRotation | None, titles: list[str]
) -> None:
    wired = services(rotation)
    status = QStatusBar()
    qtbot.addWidget(status)

    tabs = application.build_tabs(config, wired, ControlsModel(wired.controls), StatusFeedback(status))
    for _, widget in tabs:
        qtbot.addWidget(widget)

    assert [title for title, _ in tabs] == titles


def test_build_window_for_the_connected_camera(qtbot: QtBot, config: Config) -> None:
    add_camera(config)
    runner = FakeRunner([(["v4l2-ctl", "-d", "/dev/video0", "--list-ctrls-menus"], LINK_2_OUTPUT)])

    window = application.build_window(config, runner)
    qtbot.addWidget(window)

    assert window.tabs.tabText(0) == "Framing"
    assert window.statusBar().currentMessage() == "Connected to /dev/video0"


def test_build_window_without_a_camera(config: Config) -> None:
    with pytest.raises(CameraError, match="No Insta360 camera found"):
        application.build_window(config, FakeRunner())


def test_build_window_when_the_camera_cannot_be_read(config: Config) -> None:
    add_camera(config)
    runner = FakeRunner([(["v4l2-ctl"], CameraError("v4l2-ctl is not installed"))])

    with pytest.raises(CameraError, match="Could not read the camera:\nv4l2-ctl is not installed"):
        application.build_window(config, runner)


def test_run_shows_the_window_and_returns_the_event_loop_status(
    qtbot: QtBot, config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_camera(config)
    runner = FakeRunner([(["v4l2-ctl", "-d", "/dev/video0", "--list-ctrls-menus"], LINK_2_OUTPUT)])
    shown: list[MainWindow] = []

    def record_show(window: MainWindow) -> None:
        shown.append(window)

    monkeypatch.setattr(MainWindow, "show", record_show)
    monkeypatch.setattr(QApplication, "exec", lambda _app: 0)

    assert app.run_gui(config, runner) == 0
    assert len(shown) == 1
    qtbot.addWidget(shown[0])


def test_run_reports_a_missing_camera(qtbot: QtBot, config: Config, fatal_messages: list[str]) -> None:
    assert application.run(config, FakeRunner()) == 1
    assert fatal_messages == ["No Insta360 camera found. Is it plugged in?"]


def test_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "link_studio", "--help"], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0
    assert "--apply" in result.stdout
