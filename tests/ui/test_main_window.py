from PySide6.QtWidgets import QLabel, QPushButton, QStatusBar, QWidget
from pytestqt.qtbot import QtBot

from link_studio.ui.main_window import MainWindow
from link_studio.ui.theme import Palette, stylesheet


def make(qtbot: QtBot, refreshed: list[bool]) -> tuple[MainWindow, QWidget, QWidget, QWidget]:
    one, two, preview = QWidget(), QWidget(), QWidget()
    window = MainWindow(
        [("framing", "One", one), ("image", "Two", two)],
        preview,
        QStatusBar(),
        camera="Insta360 on /dev/video0",
        palette=Palette(),
        on_refresh=lambda: refreshed.append(True),
    )
    qtbot.addWidget(window)
    return window, one, two, preview


def test_sidebar_lists_the_pages_and_opens_the_first(qtbot: QtBot) -> None:
    window, one, _, _ = make(qtbot, [])

    assert window.titles() == ["One", "Two"]
    assert window.pages.currentWidget() is one


def test_choosing_a_page_keeps_the_preview_in_view(qtbot: QtBot) -> None:
    window, _, two, preview = make(qtbot, [])
    window.show()

    window.nav.button(1).click()

    assert window.pages.currentWidget() is two
    assert preview.isVisible()


def test_sidebar_shows_the_camera_and_refreshes_it(qtbot: QtBot) -> None:
    refreshed: list[bool] = []
    window, _, _, _ = make(qtbot, refreshed)

    [refresh] = [b for b in window.findChildren(QPushButton) if b.text() == "Refresh"]
    refresh.click()

    assert refreshed == [True]
    assert "Insta360 on /dev/video0" in [label.text() for label in window.findChildren(QLabel)]


def test_stylesheet_uses_the_palette() -> None:
    palette = Palette(accent="#123456")

    assert "#123456" in stylesheet(palette)
