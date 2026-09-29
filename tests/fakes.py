"""In-memory implementations of every port, for tests."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import replace

from link_studio.domain import (
    CameraError,
    CameraMode,
    Control,
    ControlKind,
    Profile,
    RotationDirection,
    TrackingFrame,
)

Responder = Callable[[Sequence[str]], str]


class FakeRunner:
    """CommandRunner that records calls and answers from a list of rules.

    Each rule pairs an argument prefix with a response. A response that is
    an exception is raised instead of returned.
    """

    def __init__(self, rules: Iterable[tuple[Sequence[str], str | Exception]] = ()) -> None:
        self.calls: list[list[str]] = []
        self.timeouts: list[float] = []
        self._rules = [(list(prefix), response) for prefix, response in rules]

    def when(self, prefix: Sequence[str], response: str | Exception) -> FakeRunner:
        self._rules.insert(0, (list(prefix), response))
        return self

    def run(self, args: Sequence[str], timeout: float = 10.0) -> str:
        call = list(args)
        self.calls.append(call)
        self.timeouts.append(timeout)
        for prefix, response in self._rules:
            if call[: len(prefix)] == prefix:
                if isinstance(response, Exception):
                    raise response
                return response
        return ""


class FakeControlBackend:
    def __init__(self, controls: Iterable[Control] = (), failing: Iterable[str] = ()) -> None:
        self._controls = {c.name: c for c in controls}
        self._failing = set(failing)
        self.writes: list[tuple[str, int]] = []

    def list_controls(self) -> list[Control]:
        return list(self._controls.values())

    def set_control(self, name: str, value: int) -> None:
        self.writes.append((name, value))
        if name in self._failing:
            raise CameraError(f"{name} refused")
        self._controls[name] = replace(self._controls[name], value=value)


class FakeTracking:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, object]] = []
        self._fail = fail

    def set_tracking(self, enabled: bool) -> None:
        self._record("tracking", enabled)

    def set_framing(self, frame: TrackingFrame) -> None:
        self._record("framing", frame)

    def set_mode(self, mode: CameraMode) -> None:
        self._record("mode", mode)

    def _record(self, name: str, value: object) -> None:
        self.calls.append((name, value))
        if self._fail:
            raise CameraError("vendor command failed")


class FakeGimbal:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int | None]] = []

    def centre(self) -> None:
        self.calls.append(("centre", None))

    def save_preset(self, slot: int) -> None:
        self.calls.append(("save", slot))

    def recall_preset(self, slot: int) -> None:
        self.calls.append(("recall", slot))


class MemoryProfileStore:
    def __init__(self, profile: Profile | None = None, error: CameraError | None = None) -> None:
        self.profile = profile
        self._error = error

    @property
    def location(self) -> str:
        return "memory"

    def load(self) -> Profile | None:
        if self._error is not None:
            raise self._error
        return self.profile

    def save(self, profile: Profile) -> None:
        self.profile = profile


class FakeAutostart:
    def __init__(self, enabled: bool = False, fail: bool = False) -> None:
        self.enabled = enabled
        self._fail = fail

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self) -> None:
        self._set(True)

    def disable(self) -> None:
        self._set(False)

    def _set(self, enabled: bool) -> None:
        if self._fail:
            raise CameraError("systemctl failed")
        self.enabled = enabled


class FakeRotation:
    def __init__(self, fail: bool = False) -> None:
        self.running = False
        self.direction: RotationDirection | None = None
        self._fail = fail

    def is_running(self) -> bool:
        return self.running

    def start(self, direction: RotationDirection) -> None:
        if self._fail:
            raise CameraError("camera busy")
        self.running = True
        self.direction = direction

    def stop(self) -> None:
        self.running = False


class SequenceLocator:
    """CameraLocator that returns each result in turn, then repeats the last."""

    def __init__(self, *results: str | None) -> None:
        self._results = list(results)
        self.calls = 0

    def find(self) -> str | None:
        index = min(self.calls, len(self._results) - 1)
        self.calls += 1
        return self._results[index]


def integer(
    name: str,
    value: int = 0,
    *,
    minimum: int = 0,
    maximum: int = 100,
    step: int = 1,
    default: int = 50,
    inactive: bool = False,
) -> Control:
    """Build an integer control with sensible defaults."""
    return Control(
        name=name,
        kind=ControlKind.INTEGER,
        minimum=minimum,
        maximum=maximum,
        step=step,
        default=default,
        value=value,
        inactive=inactive,
    )
