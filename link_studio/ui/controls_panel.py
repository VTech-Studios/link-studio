"""A panel of control rows, kept in sync with the ControlsModel."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..domain import Control
from .controls_model import ControlsModel
from .editors import ControlEditor, create_editor
from .feedback import StatusFeedback
from .layout import button, label

Formatter = Callable[[int], str]
LABEL_WIDTH = 140
READOUT_WIDTH = 56


class ControlRow(QWidget):
    """Label, editor, optional readout and a reset button for one control."""

    changed = Signal(str, int)

    def __init__(self, control: Control, formatter: Formatter | None = None) -> None:
        super().__init__()
        self._name = control.name
        self._formatter = formatter
        self._editor: ControlEditor = create_editor(control)
        self._editor.edited.connect(self._on_edited)
        self._readout = QLabel()
        self._readout.setMinimumWidth(READOUT_WIDTH)
        self._readout.setVisible(formatter is not None)

        name = label(control.label)
        name.setFixedWidth(LABEL_WIDTH)
        name.setWordWrap(True)
        reset = button("Reset", lambda: self._on_edited(control.default), "ghost")
        reset.setToolTip(f"Default: {control.default}")
        reset.setVisible(control.has_valid_default)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(name)
        layout.addWidget(self._editor, 1)
        layout.addWidget(self._readout)
        layout.addWidget(reset)
        self.display(control)

    def display(self, control: Control) -> None:
        """Show the camera's current state without sending it back.

        Inactive controls are disabled because an automatic mode overrides
        them and edits would have no effect.
        """
        self._editor.display(control)
        self._show_readout(control.value)
        self.setEnabled(not control.inactive)

    def _on_edited(self, value: int) -> None:
        self._show_readout(value)
        self.changed.emit(self._name, value)

    def _show_readout(self, value: int) -> None:
        if self._formatter is not None:
            self._readout.setText(self._formatter(value))


class ControlsPanel(QWidget):
    """Rows for every control accepted by `include`.

    Rows are built from what the camera reports, so a firmware update that
    adds a control shows up without code changes.
    """

    def __init__(
        self,
        model: ControlsModel,
        feedback: StatusFeedback,
        include: Callable[[Control], bool],
        formatters: Mapping[str, Formatter] | None = None,
    ) -> None:
        super().__init__()
        self._model = model
        self._feedback = feedback
        self._include = include
        self._formatters = formatters or {}
        self._rows: dict[str, ControlRow] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        model.updated.connect(self._on_updated)
        self._on_updated(model.controls())

    def rows(self) -> dict[str, ControlRow]:
        return dict(self._rows)

    def _on_updated(self, controls: list[Control]) -> None:
        for control in filter(self._include, controls):
            row = self._rows.get(control.name)
            if row is None:
                self._add_row(control)
            else:
                row.display(control)

    def _add_row(self, control: Control) -> None:
        row = ControlRow(control, self._formatters.get(control.name))
        row.changed.connect(self._on_changed)
        self._rows[control.name] = row
        self._layout.addWidget(row)

    def _on_changed(self, name: str, value: int) -> None:
        self._feedback.run(f"{name} = {value}", lambda: self._model.set(name, value))
