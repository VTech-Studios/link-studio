from link_studio.domain import CameraError, Profile
from link_studio.services.on_connect import ApplyOnConnect, Timing
from link_studio.services.startup import StartupService
from tests.fakes import FakeControlBackend, FakeTracking, MemoryProfileStore, SequenceLocator, integer

TIMING = Timing(wait_seconds=2.0, poll_seconds=0.5, settle_seconds=3.0)


class FakeClock:
    """A clock that only moves when the code under test sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def run(
    locator: SequenceLocator,
    store: MemoryProfileStore,
    tracking: FakeTracking | None = None,
    controls: FakeControlBackend | None = None,
) -> tuple[int, list[str], FakeClock, list[str]]:
    clock = FakeClock()
    messages: list[str] = []
    devices: list[str] = []

    def service_for(device: str) -> StartupService:
        devices.append(device)
        return StartupService(controls or FakeControlBackend(), tracking or FakeTracking(), store)

    status = ApplyOnConnect(
        locator, service_for, messages.append, timing=TIMING, sleep=clock.sleep, clock=clock.time
    ).run()
    return status, messages, clock, devices


def test_waits_for_the_camera_then_settles_before_applying() -> None:
    tracking = FakeTracking()

    status, messages, clock, devices = run(
        SequenceLocator(None, None, "/dev/video0"), MemoryProfileStore(Profile()), tracking
    )

    assert status == 0
    assert devices == ["/dev/video0"]
    assert clock.sleeps == [0.5, 0.5, 3.0]
    assert tracking.calls
    assert messages == ["link-studio: startup settings applied to /dev/video0"]


def test_gives_up_when_the_camera_never_appears() -> None:
    locator = SequenceLocator(None)

    status, messages, clock, devices = run(locator, MemoryProfileStore(Profile()))

    assert status == 1
    assert devices == []
    assert sum(clock.sleeps) == TIMING.wait_seconds
    assert messages == ["link-studio: the camera did not appear"]


def test_reports_settings_that_failed() -> None:
    controls = FakeControlBackend([integer("brightness")], failing={"brightness"})

    status, messages, _, _ = run(
        SequenceLocator("/dev/video0"),
        MemoryProfileStore(Profile(controls={"brightness": 1})),
        controls=controls,
    )

    assert status == 1
    assert messages == ["link-studio: could not apply: brightness"]


def test_reports_a_missing_or_broken_profile() -> None:
    status, messages, _, _ = run(
        SequenceLocator("/dev/video0"),
        MemoryProfileStore(error=CameraError("startup.json is not valid JSON")),
    )

    assert status == 1
    assert messages == ["link-studio: startup.json is not valid JSON"]
