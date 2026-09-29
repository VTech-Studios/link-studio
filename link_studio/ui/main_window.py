"""The main window: tabs plus a status bar with a refresh button."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtWidgets import QMainWindow, QPushButton, QStatusBar, QTabWidget, QWidget

WINDOW_SIZE = (760, 620)


class MainWindow(QMainWindow):
    """Assembles tabs it is given; it does not know what any of them do."""

    def __init__(
        self,
        tabs: Sequence[tuple[str, QWidget]],
        status_bar: QStatusBar,
        on_refresh: Callable[[], object],
    ) -> None:
        super().__init__()
        self.setWindowTitle("Link Studio")
        self.resize(*WINDOW_SIZE)

        self.tabs = QTabWidget()
        for title, widget in tabs:
            self.tabs.addTab(widget, title)
        self.setCentralWidget(self.tabs)

        refresh = QPushButton("Refresh")
        refresh.setToolTip("Re-read every value from the camera")
        refresh.clicked.connect(on_refresh)
        status_bar.addPermanentWidget(refresh)
        self.setStatusBar(status_bar)
