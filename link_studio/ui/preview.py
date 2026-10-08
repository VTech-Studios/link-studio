"""Preview panel: a live picture from the camera, beside whichever page is open."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QCamera, QCameraDevice, QMediaCaptureSession, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from .feedback import FAILURE_TIMEOUT_MS, StatusFeedback
from .icons import pixmap
from .layout import PAGE_MARGINS, label, note
from .theme import Palette

IDLE_ICON_SIZE = 44


class PreviewPanel(QWidget):
    """Opens the camera only while the preview is on.

    A camera can stream to one program at a time. Holding it open whenever
    the window is open would lock out the call site this app exists to help,
    so the panel stays visible but idle until it is switched on.
    """

    def __init__(
        self,
        camera_name: str,
        feedback: StatusFeedback,
        palette: Palette,
        devices: Callable[[], Sequence[QCameraDevice]] = QMediaDevices.videoInputs,
    ) -> None:
        super().__init__()
        self.setObjectName("preview")
        self._camera_name = camera_name
        self._feedback = feedback
        self._devices = devices
        self._camera: QCamera | None = None
        self._video = QVideoWidget()
        self._session = QMediaCaptureSession()
        self._session.setVideoOutput(self._video)
        self._idle = self._idle_screen(palette)

        self.toggle = QPushButton("Start preview")
        self.toggle.setObjectName("primary")
        self.toggle.setCheckable(True)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.toggled.connect(self._on_toggled)
        self.live = label("LIVE", "liveBadge")
        self.live.setVisible(False)
        self.monitor = QStackedWidget()
        self.monitor.setObjectName("monitor")
        self.monitor.addWidget(self._idle)
        self.monitor.addWidget(self._video)

        header = QHBoxLayout()
        header.addWidget(label("Preview", "title"))
        header.addWidget(self.live)
        header.addStretch()
        header.addWidget(self.toggle)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*PAGE_MARGINS)
        layout.setSpacing(14)
        layout.addLayout(header)
        layout.addWidget(self.monitor, 1)
        layout.addWidget(
            note(
                "The preview fails while a call site or Rotated cam is using the camera. "
                "The settings still work without it."
            )
        )

    def is_showing_video(self) -> bool:
        return self.monitor.currentWidget() is self._video

    def _idle_screen(self, palette: Palette) -> QWidget:
        screen = QWidget()
        image = QLabel()
        image.setPixmap(pixmap("camera", palette.faint, IDLE_ICON_SIZE))
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = label("Preview is off", "idleTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = note("Start it to see changes as you make them. Stopping it frees the camera for calls.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(screen)
        layout.addStretch()
        layout.addWidget(image)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addStretch()
        return screen

    def _on_toggled(self, on: bool) -> None:
        if on:
            self._start()
        else:
            self._stop()

    def _start(self) -> None:
        device = self._find_device()
        if device is None:
            self._fail(f"No {self._camera_name} camera found for preview")
            return
        self._camera = QCamera(device)
        self._camera.errorOccurred.connect(self._on_error)
        self._session.setCamera(self._camera)
        self._camera.start()
        self._show_running(True)

    def _stop(self) -> None:
        if self._camera is not None:
            self._camera.stop()
            self._camera = None
        self._show_running(False)

    def _show_running(self, running: bool) -> None:
        self.toggle.setText("Stop preview" if running else "Start preview")
        self.live.setVisible(running)
        self.monitor.setCurrentWidget(self._video if running else self._idle)

    def _find_device(self) -> QCameraDevice | None:
        return next((d for d in self._devices() if self._camera_name in d.description()), None)

    def _on_error(self, _error: QCamera.Error, message: str) -> None:
        self._fail(f"Preview: {message}")

    def _fail(self, message: str) -> None:
        self._feedback.show(message, FAILURE_TIMEOUT_MS)
        self.toggle.setChecked(False)
