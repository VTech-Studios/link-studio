"""Editors for a single control value, one class per control kind."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QSlider, QSpinBox, QWidget

from ..domain import Control, ControlKind

SLIDER_DEBOUNCE_MS = 120
SLIDER_PAGE_STEPS = 10
SPIN_WIDTH = 84


class ControlEditor(QWidget):
    """Base editor. Emits `edited` with a value the user chose.

    Subclasses implement `display`, which shows a value without emitting,
    so refreshing from the camera never echoes a write back to it.
    """

    edited = Signal(int)

    def __init__(self, control: Control) -> None:
        super().__init__()
        self._control = control

    def display(self, control: Control) -> None:
        raise NotImplementedError


class BooleanEditor(ControlEditor):
    def __init__(self, control: Control) -> None:
        super().__init__(control)
        self._box = QCheckBox("On")
        self._box.toggled.connect(lambda on: self.edited.emit(int(on)))
        _single(self, self._box)

    def display(self, control: Control) -> None:
        self._box.blockSignals(True)
        self._box.setChecked(bool(control.value))
        self._box.blockSignals(False)


class MenuEditor(ControlEditor):
    def __init__(self, control: Control) -> None:
        super().__init__(control)
        self._combo = QComboBox()
        for value, text in control.menu.items():
            self._combo.addItem(text, value)
        self._combo.activated.connect(self._on_activated)
        _single(self, self._combo)

    def display(self, control: Control) -> None:
        index = self._combo.findData(control.value)
        if index >= 0:
            self._combo.blockSignals(True)
            self._combo.setCurrentIndex(index)
            self._combo.blockSignals(False)

    def _on_activated(self, index: int) -> None:
        self.edited.emit(int(self._combo.itemData(index)))


class IntegerEditor(ControlEditor):
    """Slider for feel, spin box for exact values.

    Slider movement is debounced so one drag sends one command, instead of
    one per pixel, which would make a gimbal stutter through every position.
    Values snap to the control's step because the camera rejects others
    (pan and tilt only accept multiples of 3600).
    """

    def __init__(self, control: Control) -> None:
        super().__init__(control)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._spin = QSpinBox()
        for widget in (self._slider, self._spin):
            widget.setRange(control.minimum, control.maximum)
            widget.setSingleStep(control.step)
        self._slider.setPageStep(control.step * SLIDER_PAGE_STEPS)
        self._spin.setFixedWidth(SPIN_WIDTH)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(SLIDER_DEBOUNCE_MS)
        self._debounce.timeout.connect(lambda: self.edited.emit(self._spin.value()))

        self._slider.valueChanged.connect(self._on_slider_moved)
        self._spin.editingFinished.connect(lambda: self.edited.emit(self._spin.value()))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._slider, 1)
        layout.addWidget(self._spin)

    def display(self, control: Control) -> None:
        self._control = control
        self._set_silently(control.value)

    def _on_slider_moved(self, value: int) -> None:
        self._set_silently(self._control.clamp(value))
        self._debounce.start()

    def _set_silently(self, value: int) -> None:
        for widget in (self._slider, self._spin):
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)


EDITORS: dict[ControlKind, type[ControlEditor]] = {
    ControlKind.BOOLEAN: BooleanEditor,
    ControlKind.MENU: MenuEditor,
    ControlKind.INTEGER: IntegerEditor,
}


def create_editor(control: Control) -> ControlEditor:
    return EDITORS[control.kind](control)


def _single(parent: QWidget, child: QWidget) -> None:
    layout = QHBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(child)
    layout.addStretch()
