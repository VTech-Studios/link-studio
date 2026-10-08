"""Startup tab: save a profile and restore it whenever the camera connects."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QWidget

from ...domain import CameraError, CameraMode, Profile
from ...ports import Autostart
from ...services.startup import StartupService
from ..controls_model import ControlsModel
from ..feedback import FAILURE_TIMEOUT_MS, StatusFeedback
from ..layout import button_row, card, fill, note, page
from .modes import MODE_LABELS


class StartupTab(QWidget):
    def __init__(
        self,
        startup: StartupService,
        autostart: Autostart,
        model: ControlsModel,
        feedback: StatusFeedback,
    ) -> None:
        super().__init__()
        self._startup = startup
        self._autostart = autostart
        self._model = model
        self._feedback = feedback

        self.tracking = QCheckBox("AI tracking on at startup")
        self.mode = QComboBox()
        for mode, label in MODE_LABELS.items():
            self.mode.addItem(label, mode)
        self.tracking.toggled.connect(self._on_tracking_toggled)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.automatic = QCheckBox("Apply automatically whenever the camera connects")
        self.automatic.setChecked(autostart.is_enabled())
        self.automatic.toggled.connect(self.set_automatic)

        fill(
            self,
            page(
                "Startup",
                "Save your setup and restore it every time the camera connects.",
                card(
                    "Settings to restore",
                    note(
                        "The camera resets when it loses power and comes back with AI tracking on. "
                        "Set it up on the other pages, choose tracking and mode here, then save. "
                        "Every picture setting, plus pan, tilt and zoom, is stored."
                    ),
                    self.tracking,
                    self.mode,
                    button_row([("Save current settings", self.save), ("Apply now", self.apply_now)]),
                    self.summary,
                ),
                card(
                    "When to restore",
                    self.automatic,
                    note(
                        "Runs at login and whenever the camera is plugged in, through a systemd "
                        "user service. No root access is needed."
                    ),
                ),
            ),
        )
        self._show_saved()

    def save(self) -> None:
        mode = CameraMode(self.mode.currentData())
        if self._feedback.run(
            "Startup settings saved", lambda: self._startup.save_current(self.tracking.isChecked(), mode)
        ):
            self._show_saved()

    def apply_now(self) -> None:
        failures: list[str] = []

        def apply() -> None:
            failures.extend(self._startup.apply_saved())
            self._model.refresh()

        if self._feedback.run("Startup settings applied", apply) and failures:
            self._feedback.show(f"Could not apply: {', '.join(failures)}", FAILURE_TIMEOUT_MS)

    def set_automatic(self, enabled: bool) -> None:
        action = self._autostart.enable if enabled else self._autostart.disable
        state = "enabled" if enabled else "disabled"
        if not self._feedback.run(f"Automatic apply {state}", action):
            self.automatic.blockSignals(True)
            self.automatic.setChecked(not enabled)
            self.automatic.blockSignals(False)

    def _on_tracking_toggled(self, on: bool) -> None:
        """Enable the mode choice only while tracking is off.

        Tracking and the modes share one camera setting, so a mode cannot be
        applied together with tracking.
        """
        self.mode.setEnabled(not on)

    def _show_saved(self) -> None:
        try:
            profile = self._startup.load()
        except CameraError as error:
            self.summary.setText(str(error))
            return
        if profile is None:
            self.summary.setText("No startup settings saved yet.")
            return
        self._show_profile(profile)

    def _show_profile(self, profile: Profile) -> None:
        self.tracking.setChecked(profile.tracking)
        self.mode.setCurrentIndex(max(0, self.mode.findData(profile.mode)))
        self.summary.setText(f"Saved: {profile.describe()}.\n{self._startup.location}")
