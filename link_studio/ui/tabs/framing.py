"""Framing tab: pan, tilt and zoom, a nudge pad, and stored presets."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from ...domain import PRESET_SLOTS, Control
from ...ports import GimbalBackend
from ..controls_model import ControlsModel
from ..controls_panel import ControlsPanel
from ..feedback import StatusFeedback
from ..layout import button, card, fill, note, page

ARCSEC_PER_DEGREE = 3600
NUDGE_DEGREES = 5
PAN = "pan_absolute"
TILT = "tilt_absolute"
ZOOM = "zoom_absolute"
FRAMING_CONTROLS = frozenset({PAN, TILT, ZOOM})
NUDGE_BUTTONS = (
    ("▲", 0, 1, TILT, 1),
    ("◀", 1, 0, PAN, -1),
    ("▶", 1, 2, PAN, 1),
    ("▼", 2, 1, TILT, -1),
)


def degrees(value: int) -> str:
    return f"{value / ARCSEC_PER_DEGREE:+.0f}°"


def magnification(value: int) -> str:
    return f"{value / 100:.2f}x"


def is_framing_control(control: Control) -> bool:
    return control.name in FRAMING_CONTROLS


class FramingTab(QWidget):
    def __init__(self, model: ControlsModel, gimbal: GimbalBackend, feedback: StatusFeedback) -> None:
        super().__init__()
        self._model = model
        self._gimbal = gimbal
        self._feedback = feedback
        self.panel = ControlsPanel(
            model, feedback, is_framing_control, {PAN: degrees, TILT: degrees, ZOOM: magnification}
        )
        fill(
            self,
            page(
                "Framing",
                "Aim and zoom the camera, and keep positions you return to.",
                card(
                    "Position and zoom",
                    self.panel,
                    note(
                        "AI tracking overrides pan and tilt. Turn it off under AI and modes to aim by hand."
                    ),
                ),
                card(f"Nudge, {NUDGE_DEGREES}° per click", self._nudge_pad()),
                card("Presets, stored in the camera", self._presets()),
            ),
        )

    def nudge(self, name: str, direction: int) -> None:
        """Move one axis by NUDGE_DEGREES, clamped to what the camera accepts."""
        control = self._model.get(name)
        if control is None:
            return
        target = control.clamp(control.value + direction * NUDGE_DEGREES * ARCSEC_PER_DEGREE)
        self._feedback.run(f"{control.label} = {degrees(target)}", lambda: self._model.set(name, target))

    def centre(self) -> None:
        self._feedback.run("Centred", self._then_refresh(self._gimbal.centre))

    def save_preset(self, slot: int) -> None:
        self._feedback.run(f"Saved preset {slot + 1}", lambda: self._gimbal.save_preset(slot))

    def recall_preset(self, slot: int) -> None:
        self._feedback.run(
            f"Moved to preset {slot + 1}", self._then_refresh(lambda: self._gimbal.recall_preset(slot))
        )

    def _nudge_pad(self) -> QWidget:
        pad = QWidget()
        grid = QGridLayout(pad)
        for text, row, column, name, direction in NUDGE_BUTTONS:
            grid.addWidget(button(text, partial(self.nudge, name, direction)), row, column)
        grid.addWidget(button("Centre", self.centre), 1, 1)
        return pad

    def _presets(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        for slot in PRESET_SLOTS:
            grid.addWidget(QLabel(f"Preset {slot + 1}"), slot, 0)
            grid.addWidget(button("Save here", partial(self.save_preset, slot)), slot, 1)
            grid.addWidget(button("Go to", partial(self.recall_preset, slot)), slot, 2)
        return container

    def _then_refresh(self, action: Callable[[], None]) -> Callable[[], None]:
        """Wrap a gimbal action so the model is re-read afterwards.

        Gimbal moves change pan and tilt without going through the model, so
        without a refresh the sliders would show stale positions.
        """

        def run() -> None:
            action()
            self._model.refresh()

        return run
