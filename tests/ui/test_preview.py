from PySide6.QtMultimedia import QCameraDevice
from PySide6.QtWidgets import QStatusBar
from pytestqt.qtbot import QtBot

from link_studio.ui.feedback import StatusFeedback
from link_studio.ui.tabs.preview import PreviewTab


def make(qtbot: QtBot, devices: list[QCameraDevice]) -> tuple[PreviewTab, QStatusBar]:
    status = QStatusBar()
    qtbot.addWidget(status)
    tab = PreviewTab("Insta360", StatusFeedback(status), devices=lambda: devices)
    qtbot.addWidget(tab)
    return tab, status


def test_starts_idle_without_holding_the_camera(qtbot: QtBot) -> None:
    tab, _ = make(qtbot, [])

    assert tab.toggle.text() == "Start preview"
    assert not tab.toggle.isChecked()


def test_missing_camera_is_reported_and_the_toggle_resets(qtbot: QtBot) -> None:
    tab, status = make(qtbot, [QCameraDevice()])

    tab.toggle.setChecked(True)

    assert status.currentMessage() == "No Insta360 camera found for preview"
    assert not tab.toggle.isChecked()
    assert tab.toggle.text() == "Start preview"
