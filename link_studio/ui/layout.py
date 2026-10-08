"""Small layout helpers shared by the pages."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

Action = tuple[str, Callable[[], object]]
PAGE_MARGINS = (28, 24, 28, 28)


def label(text: str, name: str = "") -> QLabel:
    """Make a label the stylesheet can find by `name`."""
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    return widget


def note(text: str) -> QLabel:
    widget = label(text, "note")
    widget.setWordWrap(True)
    return widget


def button(text: str, action: Callable[[], object], name: str = "") -> QPushButton:
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if name:
        widget.setObjectName(name)
    widget.clicked.connect(action)
    return widget


def button_row(actions: Sequence[Action]) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    for text, action in actions:
        layout.addWidget(button(text, action))
    return row


def card(title: str, *widgets: QWidget) -> QFrame:
    """Build a rounded panel with a small capitalised heading, grouping related controls."""
    box = QFrame()
    box.setObjectName("card")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(10)
    layout.addWidget(label(title.upper(), "section"))
    for widget in widgets:
        layout.addWidget(widget)
    return box


def page(title: str, subtitle: str, *widgets: QWidget) -> QScrollArea:
    """Build a titled page that scrolls, stacking widgets from the top.

    Every page scrolls because the settings column shares the window with
    the preview, so even short pages can outgrow it on a small screen.
    """
    body = QWidget()
    body.setObjectName("pageBody")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(*PAGE_MARGINS)
    layout.setSpacing(16)
    header = QVBoxLayout()
    header.setSpacing(2)
    header.addWidget(label(title, "title"))
    header.addWidget(note(subtitle))
    layout.addLayout(header)
    for widget in widgets:
        layout.addWidget(widget)
    layout.addStretch()

    scroll = QScrollArea()
    scroll.setObjectName("page")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(body)
    return scroll


def fill(parent: QWidget, child: QWidget) -> None:
    """Make `child` fill `parent` edge to edge."""
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(child)
