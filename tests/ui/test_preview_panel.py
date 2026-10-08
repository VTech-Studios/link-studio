from PySide6.QtMultimedia import QCameraDevice
from PySide6.QtWidgets import QStatusBar
from pytestqt.qtbot import QtBot

from link_studio.ui.feedback import StatusFeedback
from link_studio.ui.preview import PreviewPanel
from link_studio.ui.theme import Palette


def make(qtbot: QtBot, devices: list[QCameraDevice]) -> tuple[PreviewPanel, QStatusBar]:
    status = QStatusBar()
    qtbot.addWidget(status)
    panel = PreviewPanel("Insta360", StatusFeedback(status), Palette(), devices=lambda: devices)
    qtbot.addWidget(panel)
    return panel, status


def test_starts_idle_without_holding_the_camera(qtbot: QtBot) -> None:
    panel, _ = make(qtbot, [])

    assert panel.toggle.text() == "Start preview"
    assert not panel.toggle.isChecked()
    assert not panel.is_showing_video()
    assert panel.live.isHidden()


def test_missing_camera_is_reported_and_the_panel_stays_idle(qtbot: QtBot) -> None:
    panel, status = make(qtbot, [QCameraDevice()])

    panel.toggle.setChecked(True)

    assert status.currentMessage() == "No Insta360 camera found for preview"
    assert not panel.toggle.isChecked()
    assert panel.toggle.text() == "Start preview"
    assert not panel.is_showing_video()
    assert panel.live.isHidden()
