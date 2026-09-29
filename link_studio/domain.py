"""Domain model: what a camera setting is, independent of how it is read.

Nothing here performs I/O or imports Qt, so every rule about controls and
profiles can be tested in isolation and shared by the GUI and the headless
`--apply` path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Any

PRESET_SLOTS = range(6)


class CameraError(RuntimeError):
    """A camera operation failed. The message is written for the user."""


class ControlKind(StrEnum):
    """The V4L2 control types this application can edit."""

    INTEGER = "int"
    BOOLEAN = "bool"
    MENU = "menu"


class CameraMode(StrEnum):
    """The camera's special framing modes.

    AI tracking and these modes share one register in the Insta360 firmware,
    so selecting any mode, including NORMAL, also switches tracking off.
    """

    NORMAL = "normal"
    DESKVIEW = "deskview"
    WHITEBOARD = "whiteboard"
    OVERHEAD = "overhead"


class TrackingFrame(StrEnum):
    """How much of the subject AI tracking keeps in frame."""

    HEAD = "head"
    HALF_BODY = "half"
    FULL_BODY = "full"


class RotationDirection(StrEnum):
    CLOCKWISE = "cw"
    ANTICLOCKWISE = "ccw"


def _empty_mapping() -> Mapping[Any, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class Control:
    """One standard (V4L2) control and its current state.

    `inactive` means an automatic mode currently overrides the control, for
    example manual focus while autofocus is on. The camera ignores or
    refuses writes to it until the automatic mode is switched off.
    """

    name: str
    kind: ControlKind
    minimum: int = 0
    maximum: int = 1
    step: int = 1
    default: int = 0
    value: int = 0
    inactive: bool = False
    menu: Mapping[int, str] = field(default_factory=_empty_mapping)

    @property
    def label(self) -> str:
        return self.name.replace("_", " ").capitalize()

    @staticmethod
    def is_automatic_name(name: str) -> bool:
        """Report whether a name is an automatic switch such as `white_balance_automatic`.

        These govern other controls, so they must be written before the
        values they govern when restoring settings.
        """
        return "auto" in name

    @property
    def has_valid_default(self) -> bool:
        """Report whether the default can actually be written back.

        The Link 2 reports power_line_frequency with default 3 and range 0..2,
        so offering a reset to it would only produce an error.
        """
        return self.minimum <= self.default <= self.maximum

    def clamp(self, value: int) -> int:
        """Return the nearest value the camera accepts: within range and on a step."""
        bounded = max(self.minimum, min(self.maximum, value))
        steps = round((bounded - self.minimum) / self.step)
        return min(self.maximum, self.minimum + steps * self.step)

    def with_menu(self, menu: Mapping[int, str]) -> Control:
        return replace(self, menu=MappingProxyType(dict(menu)))


@dataclass(frozen=True)
class Profile:
    """Settings to restore when the camera connects."""

    tracking: bool = False
    mode: CameraMode = CameraMode.NORMAL
    controls: Mapping[str, int] = field(default_factory=_empty_mapping)

    def to_dict(self) -> dict[str, Any]:
        return {"tracking": self.tracking, "mode": self.mode.value, "controls": dict(self.controls)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Profile:
        """Build a profile from stored data.

        Raises CameraError for malformed data, so a hand-edited or corrupted
        file produces a readable message instead of a traceback.
        """
        try:
            controls = {str(name): int(value) for name, value in data.get("controls", {}).items()}
            return cls(
                tracking=bool(data.get("tracking", False)),
                mode=CameraMode(data.get("mode", CameraMode.NORMAL)),
                controls=MappingProxyType(controls),
            )
        except (AttributeError, TypeError, ValueError) as error:
            raise CameraError(f"Saved startup settings are invalid: {error}") from error

    def describe(self) -> str:
        state = "tracking on" if self.tracking else f"tracking off, {self.mode.value} mode"
        return f"{state}, {len(self.controls)} picture and position settings"
