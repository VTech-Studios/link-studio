"""Interfaces (ports) between the application and the outside world.

Services and widgets depend on these protocols, never on the concrete
adapters in `infrastructure`. That keeps each class focused on one job,
lets the composition root in `app.py` decide what is real, and lets tests
substitute fakes without patching.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from .domain import CameraMode, Control, Profile, RotationDirection, TrackingFrame


class CommandRunner(Protocol):
    def run(self, args: Sequence[str], timeout: float = 10.0) -> str:
        """Run a command and return its standard output.

        Raises CameraError if the command is missing, times out, or fails.
        """
        ...


class CameraLocator(Protocol):
    def find(self) -> str | None:
        """Return the camera's capture device path, or None if absent."""
        ...


class ControlBackend(Protocol):
    """Standard V4L2 controls: brightness, pan, tilt, zoom, focus..."""

    def list_controls(self) -> list[Control]: ...

    def set_control(self, name: str, value: int) -> None: ...


class TrackingBackend(Protocol):
    """AI tracking and the special modes that share its register."""

    def set_tracking(self, enabled: bool) -> None: ...

    def set_framing(self, frame: TrackingFrame) -> None: ...

    def set_mode(self, mode: CameraMode) -> None: ...


class GimbalBackend(Protocol):
    """Gimbal positions stored in the camera itself."""

    def centre(self) -> None: ...

    def save_preset(self, slot: int) -> None: ...

    def recall_preset(self, slot: int) -> None: ...


class ProfileStore(Protocol):
    def load(self) -> Profile | None:
        """Return the saved profile, or None if nothing has been saved."""
        ...

    def save(self, profile: Profile) -> None: ...

    @property
    def location(self) -> str: ...


class Autostart(Protocol):
    """Re-apply the profile automatically whenever the camera connects."""

    def is_enabled(self) -> bool: ...

    def enable(self) -> None: ...

    def disable(self) -> None: ...


class RotationService(Protocol):
    """A virtual camera showing a sideways camera upright."""

    def is_running(self) -> bool: ...

    def start(self, direction: RotationDirection) -> None: ...

    def stop(self) -> None: ...
