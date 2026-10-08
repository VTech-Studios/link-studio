"""Builds and runs the Qt application."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QStatusBar

from ..config import Config
from ..domain import CameraError
from ..ports import CommandRunner
from ..wiring import Services, build_locator, build_services
from .controls_model import ControlsModel
from .feedback import StatusFeedback
from .main_window import MainWindow, Page
from .preview import PreviewPanel
from .tabs.framing import FramingTab
from .tabs.image import ImageTab
from .tabs.modes import ModesTab
from .tabs.rotation import RotationTab
from .tabs.startup import StartupTab
from .theme import Palette, stylesheet

APP_NAME = "Link Studio"
PALETTE = Palette()


def build_pages(services: Services, model: ControlsModel, feedback: StatusFeedback) -> list[Page]:
    pages: list[Page] = [
        ("framing", "Framing", FramingTab(model, services.vendor, feedback)),
        ("image", "Image", ImageTab(model, feedback)),
        ("modes", "AI and modes", ModesTab(services.vendor, feedback)),
    ]
    if services.rotation is not None:
        pages.append(("rotation", "Rotated cam", RotationTab(services.rotation, feedback)))
    pages.append(("startup", "Startup", StartupTab(services.startup, services.autostart, model, feedback)))
    return pages


def build_window(config: Config, runner: CommandRunner) -> MainWindow:
    """Wire the window for the connected camera.

    Raises CameraError, with a message for the user, when there is no
    camera or it cannot be read. Building is separate from running so the
    whole wiring can be tested without starting Qt's event loop.
    """
    device = build_locator(config).find()
    if device is None:
        raise CameraError(f"No {config.camera_name} camera found. Is it plugged in?")

    services = build_services(config, device, runner)
    model = ControlsModel(services.controls)
    try:
        model.refresh()
    except CameraError as error:
        raise CameraError(f"Could not read the camera:\n{error}") from error

    status_bar = QStatusBar()
    feedback = StatusFeedback(status_bar)
    window = MainWindow(
        build_pages(services, model, feedback),
        PreviewPanel(config.camera_name, feedback, PALETTE),
        status_bar,
        camera=f"{config.camera_name} on {device}",
        palette=PALETTE,
        on_refresh=lambda: feedback.run("Refreshed", model.refresh),
    )
    feedback.show(f"Connected to {device}")
    return window


def run(config: Config, runner: CommandRunner) -> int:
    """Show the window and run the event loop until it closes.

    An existing QApplication is reused because Qt allows only one per process.
    """
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon.fromTheme("camera-web"))
    app.setStyleSheet(stylesheet(PALETTE))
    try:
        window = build_window(config, runner)
    except CameraError as error:
        QMessageBox.critical(None, APP_NAME, str(error))
        return 1
    window.show()
    return app.exec()
