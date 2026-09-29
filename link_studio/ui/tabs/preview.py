"""Preview tab: a live picture from the camera."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtMultimedia import QCamera, QCameraDevice, QMediaCaptureSession, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ..feedback import FAILURE_TIMEOUT_MS, StatusFeedback
from ..layout import note


class PreviewTab(QWidget):
    """Opens the camera only while the preview is on.

    A camera can stream to one program at a time. Holding it open while
    the tab is idle would lock out the call site this app exists to help.
    """

    def __init__(
        self,
        camera_name: str,
        feedback: StatusFeedback,
        devices: Callable[[], Sequence[QCameraDevice]] = QMediaDevices.videoInputs,
    ) -> None:
        super().__init__()
        self._camera_name = camera_name
        self._feedback = feedback
        self._devices = devices
        self._camera: QCamera | None = None
        self._video = QVideoWidget()
        self._session = QMediaCaptureSession()
        self._session.setVideoOutput(self._video)

        self.toggle = QPushButton("Start preview")
        self.toggle.setCheckable(True)
        self.toggle.toggled.connect(self._on_toggled)

        layout = QVBoxLayout(self)
        layout.addWidget(self._video, 1)
        layout.addWidget(self.toggle)
        layout.addWidget(
            note(
                "The preview fails while a call site or Rotated Cam is using the camera. "
                "The controls on the other tabs still work."
            )
        )

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
        self.toggle.setText("Stop preview")

    def _stop(self) -> None:
        if self._camera is not None:
            self._camera.stop()
            self._camera = None
        self.toggle.setText("Start preview")

    def _find_device(self) -> QCameraDevice | None:
        return next((d for d in self._devices() if self._camera_name in d.description()), None)

    def _on_error(self, _error: QCamera.Error, message: str) -> None:
        self._fail(f"Preview: {message}")

    def _fail(self, message: str) -> None:
        self._feedback.show(message, FAILURE_TIMEOUT_MS)
        self.toggle.setChecked(False)
