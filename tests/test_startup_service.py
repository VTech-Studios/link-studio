import pytest

from link_studio.domain import CameraError, CameraMode, Profile
from link_studio.services.startup import StartupService
from tests.fakes import FakeControlBackend, FakeTracking, MemoryProfileStore, integer


def service(
    controls: FakeControlBackend | None = None,
    tracking: FakeTracking | None = None,
    store: MemoryProfileStore | None = None,
) -> StartupService:
    return StartupService(
        controls or FakeControlBackend(), tracking or FakeTracking(), store or MemoryProfileStore()
    )


class TestSaveCurrent:
    def test_stores_active_controls_with_chosen_tracking_and_mode(self) -> None:
        controls = FakeControlBackend(
            [
                integer("brightness", 60),
                integer("white_balance_temperature", 3200, inactive=True),
                integer("zoom_absolute", 150),
            ]
        )
        store = MemoryProfileStore()

        saved = service(controls=controls, store=store).save_current(False, CameraMode.WHITEBOARD)

        assert store.profile == saved
        assert saved.mode is CameraMode.WHITEBOARD
        assert dict(saved.controls) == {"brightness": 60, "zoom_absolute": 150}


class TestApply:
    def test_tracking_off_is_written_as_the_mode(self) -> None:
        tracking = FakeTracking()

        service(tracking=tracking).apply(Profile(tracking=False, mode=CameraMode.DESKVIEW))

        assert tracking.calls == [("mode", CameraMode.DESKVIEW)]

    def test_tracking_on_writes_only_tracking(self) -> None:
        tracking = FakeTracking()

        service(tracking=tracking).apply(Profile(tracking=True, mode=CameraMode.DESKVIEW))

        assert tracking.calls == [("tracking", True)]

    def test_automatic_switches_are_written_before_the_values_they_govern(self) -> None:
        controls = FakeControlBackend(
            [
                integer("white_balance_temperature"),
                integer("white_balance_automatic"),
                integer("brightness"),
            ]
        )
        profile = Profile(
            controls={"white_balance_temperature": 3200, "brightness": 55, "white_balance_automatic": 0}
        )

        service(controls=controls).apply(profile)

        assert controls.writes[0] == ("white_balance_automatic", 0)
        assert set(controls.writes[1:]) == {("white_balance_temperature", 3200), ("brightness", 55)}

    def test_continues_past_failures_and_reports_them(self) -> None:
        controls = FakeControlBackend([integer("brightness"), integer("contrast")], failing={"brightness"})

        failures = service(controls=controls, tracking=FakeTracking(fail=True)).apply(
            Profile(controls={"brightness": 10, "contrast": 20})
        )

        assert failures == ["tracking", "brightness"]
        assert ("contrast", 20) in controls.writes

    def test_success_reports_no_failures(self) -> None:
        controls = FakeControlBackend([integer("brightness")])

        assert service(controls=controls).apply(Profile(controls={"brightness": 10})) == []


class TestApplySaved:
    def test_applies_the_stored_profile(self) -> None:
        tracking = FakeTracking()
        store = MemoryProfileStore(Profile(tracking=True))

        service(tracking=tracking, store=store).apply_saved()

        assert tracking.calls == [("tracking", True)]

    def test_without_a_saved_profile(self) -> None:
        with pytest.raises(CameraError, match="No startup settings"):
            service().apply_saved()


def test_load_and_location_delegate_to_the_store() -> None:
    store = MemoryProfileStore(Profile(tracking=True))

    startup = service(store=store)

    assert startup.load() == store.profile
    assert startup.location == "memory"
