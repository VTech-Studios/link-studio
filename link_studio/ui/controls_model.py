"""The camera's current control values, shared by every view that shows them."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from ..domain import Control
from ..ports import ControlBackend


class ControlsModel(QObject):
    """Single source of truth for control values.

    Views never read the camera themselves. They listen for `updated`, so a
    change made in one place (a slider, a preset, applying a profile) is
    reflected everywhere after one read, and views stay unaware of each other.
    """

    updated = Signal(list)

    def __init__(self, backend: ControlBackend) -> None:
        super().__init__()
        self._backend = backend
        self._controls: dict[str, Control] = {}

    def controls(self) -> list[Control]:
        return list(self._controls.values())

    def get(self, name: str) -> Control | None:
        return self._controls.get(name)

    def refresh(self) -> None:
        """Re-read every control from the camera and notify views."""
        self._controls = {c.name: c for c in self._backend.list_controls()}
        self.updated.emit(self.controls())

    def set(self, name: str, value: int) -> None:
        """Write one control, then refresh.

        Refreshing picks up side effects: switching automatic white balance
        off makes the temperature control editable.
        """
        self._backend.set_control(name, value)
        self.refresh()
