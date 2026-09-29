"""Rotated cam tab: start and stop the `cam-rotate` virtual camera."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

from ...domain import RotationDirection
from ...ports import RotationService
from ..feedback import StatusFeedback
from ..layout import button_row, fill, group, note, page


class RotationTab(QWidget):
    def __init__(self, rotation: RotationService, feedback: StatusFeedback) -> None:
        super().__init__()
        self._rotation = rotation
        self._feedback = feedback
        self.status = QLabel()
        fill(
            self,
            page(
                group(
                    "Virtual camera for a camera turned on its side",
                    self.status,
                    button_row(
                        [
                            ("Start (clockwise)", lambda: self.start(RotationDirection.CLOCKWISE)),
                            ("Start (anticlockwise)", lambda: self.start(RotationDirection.ANTICLOCKWISE)),
                            ("Stop", self.stop),
                        ]
                    ),
                    note(
                        "While running, Rotated Cam holds the real camera, so call sites must pick "
                        '"Rotated Cam". Stop it to use the camera directly again.'
                    ),
                )
            ),
        )
        self.update_status()

    def start(self, direction: RotationDirection) -> None:
        self._feedback.run("Rotated Cam started", lambda: self._rotation.start(direction))
        self.update_status()

    def stop(self) -> None:
        self._feedback.run("Rotated Cam stopped", self._rotation.stop)
        self.update_status()

    def update_status(self) -> None:
        running = self._rotation.is_running()
        self.status.setText("Rotated Cam is running." if running else "Rotated Cam is off.")
