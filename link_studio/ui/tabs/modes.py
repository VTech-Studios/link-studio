"""AI and modes tab: tracking, tracking framing and the special camera modes."""

from __future__ import annotations

from functools import partial

from PySide6.QtWidgets import QWidget

from ...domain import CameraMode, TrackingFrame
from ...ports import TrackingBackend
from ..feedback import StatusFeedback
from ..layout import button_row, fill, group, note, page

FRAME_LABELS = {
    TrackingFrame.HEAD: "Head",
    TrackingFrame.HALF_BODY: "Half body",
    TrackingFrame.FULL_BODY: "Full body",
}
MODE_LABELS = {
    CameraMode.NORMAL: "Normal",
    CameraMode.DESKVIEW: "DeskView",
    CameraMode.WHITEBOARD: "Whiteboard",
    CameraMode.OVERHEAD: "Overhead",
}


class ModesTab(QWidget):
    """Tracking, framing and mode controls.

    These are buttons rather than toggles because the camera cannot report
    most of these states back, and a toggle showing a guessed state would
    mislead.
    """

    def __init__(self, tracking: TrackingBackend, feedback: StatusFeedback) -> None:
        super().__init__()
        self._tracking = tracking
        self._feedback = feedback
        fill(
            self,
            page(
                group(
                    "AI tracking",
                    button_row(
                        [
                            ("Tracking on", lambda: self.set_tracking(True)),
                            ("Tracking off", lambda: self.set_tracking(False)),
                        ]
                    ),
                    note(
                        "Tracking assumes the camera is upright. Turn it off if the camera is on its "
                        "side, or it will follow you along the wrong axis and shake."
                    ),
                ),
                group(
                    "Tracking framing",
                    button_row(
                        [(label, partial(self.set_framing, frame)) for frame, label in FRAME_LABELS.items()]
                    ),
                ),
                group(
                    "Camera mode",
                    button_row(
                        [(label, partial(self.set_mode, mode)) for mode, label in MODE_LABELS.items()]
                    ),
                    note(
                        "Tracking and these modes share one setting in the camera, so choosing a mode "
                        "turns tracking off. Hand gestures are handled by the camera's firmware and "
                        "cannot be disabled from Linux."
                    ),
                ),
            ),
        )

    def set_tracking(self, enabled: bool) -> None:
        state = "on" if enabled else "off"
        self._feedback.run(f"AI tracking {state}", lambda: self._tracking.set_tracking(enabled))

    def set_framing(self, frame: TrackingFrame) -> None:
        self._feedback.run(f"Framing: {FRAME_LABELS[frame]}", lambda: self._tracking.set_framing(frame))

    def set_mode(self, mode: CameraMode) -> None:
        self._feedback.run(f"Mode: {MODE_LABELS[mode]}", lambda: self._tracking.set_mode(mode))
