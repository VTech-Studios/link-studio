"""Reports the outcome of camera actions to the user."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStatusBar

from ..domain import CameraError

SUCCESS_TIMEOUT_MS = 4000
FAILURE_TIMEOUT_MS = 8000


class StatusFeedback:
    """Runs actions and shows their result in the status bar.

    Every button in the application goes through `run`, so failures are
    reported the same way everywhere and a camera error never escapes into
    Qt's event loop, where it would be printed and otherwise ignored.
    """

    def __init__(self, status_bar: QStatusBar) -> None:
        self._status_bar = status_bar

    def run(self, description: str, action: Callable[[], object]) -> bool:
        """Run `action`, returning True if it succeeded."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            action()
        except CameraError as error:
            self.show(f"Failed: {description}: {error}", FAILURE_TIMEOUT_MS)
            return False
        finally:
            QApplication.restoreOverrideCursor()
        self.show(description, SUCCESS_TIMEOUT_MS)
        return True

    def show(self, message: str, timeout_ms: int = SUCCESS_TIMEOUT_MS) -> None:
        self._status_bar.showMessage(message, timeout_ms)
