"""Saving and restoring the camera's startup profile."""

from __future__ import annotations

from types import MappingProxyType

from ..domain import CameraError, CameraMode, Control, Profile
from ..ports import ControlBackend, ProfileStore, TrackingBackend


class StartupService:
    """Captures the camera's state into a profile and applies it back."""

    def __init__(self, controls: ControlBackend, tracking: TrackingBackend, store: ProfileStore) -> None:
        self._controls = controls
        self._tracking = tracking
        self._store = store

    @property
    def location(self) -> str:
        return self._store.location

    def load(self) -> Profile | None:
        return self._store.load()

    def save_current(self, tracking: bool, mode: CameraMode) -> Profile:
        """Save the camera's current controls with the chosen tracking and mode.

        Inactive controls are left out: an automatic mode is overriding them,
        and the camera would refuse them when the profile is applied.
        """
        values = {c.name: c.value for c in self._controls.list_controls() if not c.inactive}
        profile = Profile(tracking=tracking, mode=mode, controls=MappingProxyType(values))
        self._store.save(profile)
        return profile

    def apply_saved(self) -> list[str]:
        """Apply the saved profile and return the names of settings that failed."""
        profile = self._store.load()
        if profile is None:
            raise CameraError("No startup settings have been saved yet.")
        return self.apply(profile)

    def apply(self, profile: Profile) -> list[str]:
        """Apply a profile, continuing past individual failures.

        Tracking is applied before any position, because tracking overrides
        pan and tilt. Exactly one of tracking or a mode is written, because
        the camera stores them in the same register and the second write
        would cancel the first.
        """
        failures = self._apply_tracking(profile)
        for name, value in self.ordered_controls(profile):
            try:
                self._controls.set_control(name, value)
            except CameraError:
                failures.append(name)
        return failures

    @staticmethod
    def ordered_controls(profile: Profile) -> list[tuple[str, int]]:
        """Order controls so automatic switches come before the values they govern.

        A manual white balance temperature is refused while automatic white
        balance is still on, so the switch has to change first.
        """
        return sorted(profile.controls.items(), key=lambda item: not Control.is_automatic_name(item[0]))

    def _apply_tracking(self, profile: Profile) -> list[str]:
        try:
            if profile.tracking:
                self._tracking.set_tracking(True)
            else:
                self._tracking.set_mode(profile.mode)
        except CameraError:
            return ["tracking"]
        return []
