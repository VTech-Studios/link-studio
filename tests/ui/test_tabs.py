import pytest
from PySide6.QtWidgets import QPushButton, QStatusBar, QWidget
from pytestqt.qtbot import QtBot

from link_studio.domain import CameraError, CameraMode, Control, Profile, RotationDirection, TrackingFrame
from link_studio.services.startup import StartupService
from link_studio.ui.controls_model import ControlsModel
from link_studio.ui.feedback import StatusFeedback
from link_studio.ui.tabs.framing import ARCSEC_PER_DEGREE, FramingTab, degrees, magnification
from link_studio.ui.tabs.image import ImageTab
from link_studio.ui.tabs.modes import ModesTab
from link_studio.ui.tabs.rotation import RotationTab
from link_studio.ui.tabs.startup import StartupTab
from tests.fakes import (
    FakeAutostart,
    FakeControlBackend,
    FakeGimbal,
    FakeRotation,
    FakeTracking,
    MemoryProfileStore,
    integer,
)


class UnpluggedBackend(FakeControlBackend):
    def list_controls(self) -> list[Control]:
        raise CameraError("camera unplugged")


def pan(value: int = 0) -> Control:
    return integer("pan_absolute", value, minimum=-522000, maximum=522000, step=3600, default=0)


@pytest.fixture
def status(qtbot: QtBot) -> QStatusBar:
    bar = QStatusBar()
    qtbot.addWidget(bar)
    return bar


@pytest.fixture
def feedback(status: QStatusBar) -> StatusFeedback:
    return StatusFeedback(status)


def camera_model(*controls: Control) -> tuple[ControlsModel, FakeControlBackend]:
    backend = FakeControlBackend(controls)
    model = ControlsModel(backend)
    model.refresh()
    return model, backend


def buttons(widget: QWidget, text: str) -> list[QPushButton]:
    return [b for b in widget.findChildren(QPushButton) if b.text() == text]


def button(widget: QWidget, text: str) -> QPushButton:
    matches = buttons(widget, text)
    assert len(matches) == 1, f"expected one {text!r} button, found {len(matches)}"
    return matches[0]


def test_formatters() -> None:
    assert degrees(-5 * ARCSEC_PER_DEGREE) == "-5°"
    assert degrees(0) == "+0°"
    assert magnification(150) == "1.50x"


class TestFramingTab:
    def test_shows_only_framing_controls(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        model, _ = camera_model(pan(), integer("brightness"))
        tab = FramingTab(model, FakeGimbal(), feedback)
        qtbot.addWidget(tab)

        assert list(tab.panel.rows()) == ["pan_absolute"]

    def test_nudge_moves_five_degrees_and_clamps(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        model, backend = camera_model(pan(518400))
        tab = FramingTab(model, FakeGimbal(), feedback)
        qtbot.addWidget(tab)

        button(tab, "◀").click()
        button(tab, "▶").click()
        button(tab, "▶").click()

        assert backend.writes == [
            ("pan_absolute", 500400),
            ("pan_absolute", 518400),
            ("pan_absolute", 522000),
        ]

    def test_nudge_without_the_control_does_nothing(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        model, backend = camera_model()
        tab = FramingTab(model, FakeGimbal(), feedback)
        qtbot.addWidget(tab)

        button(tab, "▲").click()

        assert backend.writes == []

    def test_gimbal_actions(self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar) -> None:
        model, _ = camera_model(pan())
        gimbal = FakeGimbal()
        tab = FramingTab(model, gimbal, feedback)
        qtbot.addWidget(tab)

        button(tab, "Centre").click()
        buttons(tab, "Save here")[2].click()
        buttons(tab, "Go to")[4].click()

        assert gimbal.calls == [("centre", None), ("save", 2), ("recall", 4)]
        assert status.currentMessage() == "Moved to preset 5"


class TestImageTab:
    def test_shows_everything_except_framing(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        model, _ = camera_model(integer("zoom_absolute", 100), integer("brightness"), integer("contrast"))
        tab = ImageTab(model, feedback)
        qtbot.addWidget(tab)

        assert sorted(tab.panel.rows()) == ["brightness", "contrast"]


class TestModesTab:
    def test_buttons_drive_the_tracking_backend(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        tracking = FakeTracking()
        tab = ModesTab(tracking, feedback)
        qtbot.addWidget(tab)

        button(tab, "Tracking off").click()
        button(tab, "Half body").click()
        button(tab, "DeskView").click()

        assert tracking.calls == [
            ("tracking", False),
            ("framing", TrackingFrame.HALF_BODY),
            ("mode", CameraMode.DESKVIEW),
        ]

    def test_failure_is_reported(self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar) -> None:
        tab = ModesTab(FakeTracking(fail=True), feedback)
        qtbot.addWidget(tab)

        button(tab, "Tracking on").click()

        assert status.currentMessage() == "Failed: AI tracking on: vendor command failed"


class TestRotationTab:
    def test_start_and_stop_update_the_status(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        rotation = FakeRotation()
        tab = RotationTab(rotation, feedback)
        qtbot.addWidget(tab)
        assert tab.status.text() == "Rotated Cam is off."

        button(tab, "Start (anticlockwise)").click()
        assert rotation.direction is RotationDirection.ANTICLOCKWISE
        assert tab.status.text() == "Rotated Cam is running."

        button(tab, "Stop").click()
        assert tab.status.text() == "Rotated Cam is off."

    def test_failed_start(self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar) -> None:
        tab = RotationTab(FakeRotation(fail=True), feedback)
        qtbot.addWidget(tab)

        button(tab, "Start (clockwise)").click()

        assert status.currentMessage() == "Failed: Rotated Cam started: camera busy"
        assert tab.status.text() == "Rotated Cam is off."


class TestStartupTab:
    def make(
        self,
        qtbot: QtBot,
        feedback: StatusFeedback,
        store: MemoryProfileStore,
        autostart: FakeAutostart | None = None,
        controls: FakeControlBackend | None = None,
    ) -> StartupTab:
        backend = controls or FakeControlBackend([integer("brightness", 60)])
        model = ControlsModel(backend)
        tab = StartupTab(
            StartupService(backend, FakeTracking(), store), autostart or FakeAutostart(), model, feedback
        )
        qtbot.addWidget(tab)
        return tab

    def test_shows_that_nothing_is_saved(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        tab = self.make(qtbot, feedback, MemoryProfileStore())

        assert tab.summary.text() == "No startup settings saved yet."

    def test_loads_the_saved_choices(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        tab = self.make(qtbot, feedback, MemoryProfileStore(Profile(tracking=True, mode=CameraMode.OVERHEAD)))

        assert tab.tracking.isChecked()
        assert tab.mode.currentData() == CameraMode.OVERHEAD
        assert not tab.mode.isEnabled()
        assert tab.summary.text().startswith("Saved: tracking on")

    def test_save_stores_current_settings_and_choices(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        store = MemoryProfileStore()
        tab = self.make(qtbot, feedback, store)
        tab.mode.setCurrentIndex(tab.mode.findData(CameraMode.WHITEBOARD))

        button(tab, "Save current settings").click()

        assert store.profile is not None
        assert store.profile.mode is CameraMode.WHITEBOARD
        assert dict(store.profile.controls) == {"brightness": 60}
        assert tab.summary.text().startswith("Saved: tracking off, whiteboard mode")

    def test_apply_now_reports_failed_settings(
        self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar
    ) -> None:
        backend = FakeControlBackend([integer("brightness")], failing={"brightness"})
        tab = self.make(
            qtbot, feedback, MemoryProfileStore(Profile(controls={"brightness": 5})), controls=backend
        )

        button(tab, "Apply now").click()

        assert status.currentMessage() == "Could not apply: brightness"

    def test_shows_a_broken_profile_instead_of_crashing(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        store = MemoryProfileStore(error=CameraError("startup.json is not valid JSON"))

        tab = self.make(qtbot, feedback, store)

        assert tab.summary.text() == "startup.json is not valid JSON"

    def test_failed_save_keeps_the_previous_summary(
        self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar
    ) -> None:
        tab = self.make(qtbot, feedback, MemoryProfileStore(), controls=UnpluggedBackend())

        button(tab, "Save current settings").click()

        assert tab.summary.text() == "No startup settings saved yet."
        assert status.currentMessage() == "Failed: Startup settings saved: camera unplugged"

    def test_apply_now_success(self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar) -> None:
        tab = self.make(qtbot, feedback, MemoryProfileStore(Profile(controls={"brightness": 70})))

        button(tab, "Apply now").click()

        assert status.currentMessage() == "Startup settings applied"

    def test_automatic_apply_toggles_autostart(self, qtbot: QtBot, feedback: StatusFeedback) -> None:
        autostart = FakeAutostart()
        tab = self.make(qtbot, feedback, MemoryProfileStore(), autostart)

        tab.automatic.setChecked(True)
        assert autostart.enabled

        tab.automatic.setChecked(False)
        assert not autostart.enabled

    def test_failed_autostart_reverts_the_checkbox(
        self, qtbot: QtBot, feedback: StatusFeedback, status: QStatusBar
    ) -> None:
        tab = self.make(qtbot, feedback, MemoryProfileStore(), FakeAutostart(fail=True))

        tab.automatic.setChecked(True)

        assert not tab.automatic.isChecked()
        assert status.currentMessage() == "Failed: Automatic apply enabled: systemctl failed"
