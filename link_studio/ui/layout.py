"""Small layout helpers shared by the tabs."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

Action = tuple[str, Callable[[], object]]


def group(title: str, *widgets: QWidget) -> QGroupBox:
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    for widget in widgets:
        layout.addWidget(widget)
    return box


def note(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: palette(placeholder-text);")
    return label


def button_row(actions: Sequence[Action]) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    for text, action in actions:
        button = QPushButton(text)
        button.clicked.connect(action)
        layout.addWidget(button)
    return row


def page(*widgets: QWidget) -> QWidget:
    """Stack widgets from the top of a tab page, leaving spare space at the bottom."""
    container = QWidget()
    layout = QVBoxLayout(container)
    for widget in widgets:
        layout.addWidget(widget)
    layout.addStretch()
    return container


def fill(parent: QWidget, child: QWidget) -> None:
    """Make `child` fill `parent` edge to edge."""
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(child)
