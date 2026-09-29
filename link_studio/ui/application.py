"""Builds and runs the Qt application."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QStatusBar, QWidget

from ..config import Config
from ..domain import CameraError
from ..ports import CommandRunner
from ..wiring import Services, build_locator, build_services
from .controls_model import ControlsModel
from .feedback import StatusFeedback
from .main_window import MainWindow
from .tabs.framing import FramingTab
from .tabs.image import ImageTab
from .tabs.modes import ModesTab
from .tabs.preview import PreviewTab
from .tabs.rotation import RotationTab
from .tabs.startup import StartupTab

APP_NAME = "Link Studio"


def build_tabs(
    config: Config, services: Services, model: ControlsModel, feedback: StatusFeedback
) -> list[tuple[str, QWidget]]:
    tabs: list[tuple[str, QWidget]] = [
        ("Framing", FramingTab(model, services.vendor, feedback)),
        ("Image", ImageTab(model, feedback)),
        ("AI and modes", ModesTab(services.vendor, feedback)),
        ("Preview", PreviewTab(config.camera_name, feedback)),
    ]
    if services.rotation is not None:
        tabs.append(("Rotated cam", RotationTab(services.rotation, feedback)))
    tabs.append(("Startup", StartupTab(services.startup, services.autostart, model, feedback)))
    return tabs


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
        build_tabs(config, services, model, feedback),
        status_bar,
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
    try:
        window = build_window(config, runner)
    except CameraError as error:
        QMessageBox.critical(None, APP_NAME, str(error))
        return 1
    window.show()
    return app.exec()
