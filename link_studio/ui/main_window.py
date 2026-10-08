"""The main window: a sidebar of pages, the open page, and the preview beside it."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .icons import icon, pixmap
from .layout import button, label
from .theme import Palette

Page = tuple[str, str, QWidget]
WINDOW_SIZE = (1280, 800)
MINIMUM_SIZE = (1000, 620)
SIDEBAR_WIDTH = 216
SETTINGS_MINIMUM_WIDTH = 440
SPLIT_SIZES = (560, 500)
LOGO_SIZE = 26


class MainWindow(QMainWindow):
    """Assembles the pages and preview it is given; it does not know what any of them do.

    The preview sits beside the pages rather than on a page of its own, so
    the picture stays in view while settings change and their effect can be
    judged as it happens.
    """

    def __init__(
        self,
        pages: Sequence[Page],
        preview: QWidget,
        status_bar: QStatusBar,
        *,
        camera: str,
        palette: Palette,
        on_refresh: Callable[[], object],
    ) -> None:
        """`pages` holds an icon name, a title and a widget for each sidebar entry, in order."""
        super().__init__()
        self.setWindowTitle("Link Studio")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*MINIMUM_SIZE)

        self.pages = QStackedWidget()
        self.pages.setMinimumWidth(SETTINGS_MINIMUM_WIDTH)
        self.nav = QButtonGroup(self)
        for _, _, widget in pages:
            self.pages.addWidget(widget)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(1)
        split.addWidget(self.pages)
        split.addWidget(preview)
        split.setSizes(list(SPLIT_SIZES))
        split.setStretchFactor(1, 1)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._sidebar(pages, camera, palette, on_refresh))
        layout.addWidget(split, 1)
        self.setCentralWidget(root)
        self.setStatusBar(status_bar)

    def titles(self) -> list[str]:
        return [entry.text().strip() for entry in self.nav.buttons()]

    def _sidebar(
        self, pages: Sequence[Page], camera: str, palette: Palette, on_refresh: Callable[[], object]
    ) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        column = QVBoxLayout(sidebar)
        column.setContentsMargins(14, 20, 14, 16)
        column.setSpacing(4)
        column.addLayout(self._brand(palette))
        column.addSpacing(22)

        for index, (icon_name, title, _) in enumerate(pages):
            entry = QPushButton(f"  {title}")
            entry.setObjectName("nav")
            entry.setCheckable(True)
            entry.setCursor(Qt.CursorShape.PointingHandCursor)
            entry.setIcon(icon(icon_name, palette.dim, palette.text))
            self.nav.addButton(entry, index)
            column.addWidget(entry)
        self.nav.idClicked.connect(self.pages.setCurrentIndex)
        self.nav.button(0).setChecked(True)
        column.addStretch()

        column.addWidget(label("CAMERA", "section"))
        device = label(camera, "device")
        device.setWordWrap(True)
        column.addWidget(device)
        column.addSpacing(6)
        refresh = button("Refresh", on_refresh)
        refresh.setIcon(icon("refresh", palette.text, size=16))
        refresh.setToolTip("Re-read every value from the camera")
        column.addWidget(refresh)
        return sidebar

    def _brand(self, palette: Palette) -> QHBoxLayout:
        logo = label("")
        logo.setPixmap(pixmap("camera", palette.accent, LOGO_SIZE))
        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(label("Link Studio", "brand"))
        names.addWidget(label("CAMERA CONTROL", "brandTag"))
        brand = QHBoxLayout()
        brand.setSpacing(10)
        brand.addWidget(logo)
        brand.addLayout(names)
        brand.addStretch()
        return brand
