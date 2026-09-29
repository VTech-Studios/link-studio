from types import MappingProxyType

import pytest

from link_studio.domain import CameraError, CameraMode, Control, ControlKind, Profile
from tests.fakes import integer


class TestControl:
    def test_label_is_readable(self) -> None:
        assert integer("white_balance_temperature").label == "White balance temperature"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(-10, 0), (0, 0), (37, 37), (100, 100), (250, 100)],
    )
    def test_clamp_keeps_value_in_range(self, value: int, expected: int) -> None:
        assert integer("brightness").clamp(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(5000, 3600), (5500, 7200), (-1700, 0), (-1900, -3600), (600000, 522000)],
    )
    def test_clamp_snaps_to_step(self, value: int, expected: int) -> None:
        pan = integer("pan_absolute", minimum=-522000, maximum=522000, step=3600, default=0)
        assert pan.clamp(value) == expected

    def test_default_outside_range_is_not_valid(self) -> None:
        assert not integer("power_line_frequency", minimum=0, maximum=2, default=3).has_valid_default
        assert integer("brightness").has_valid_default

    @pytest.mark.parametrize(
        ("name", "automatic"),
        [
            ("white_balance_automatic", True),
            ("focus_automatic_continuous", True),
            ("white_balance_temperature", False),
            ("brightness", False),
        ],
    )
    def test_is_automatic_name(self, name: str, automatic: bool) -> None:
        assert Control.is_automatic_name(name) is automatic

    def test_with_menu_copies_and_freezes_entries(self) -> None:
        entries = {0: "Disabled", 1: "50 Hz"}
        control = Control("power_line_frequency", ControlKind.MENU).with_menu(entries)
        entries[2] = "60 Hz"

        assert dict(control.menu) == {0: "Disabled", 1: "50 Hz"}
        assert isinstance(control.menu, MappingProxyType)


class TestProfile:
    def test_round_trips_through_dict(self) -> None:
        profile = Profile(tracking=True, mode=CameraMode.DESKVIEW, controls={"zoom_absolute": 150})

        restored = Profile.from_dict(profile.to_dict())

        assert restored.tracking is True
        assert restored.mode is CameraMode.DESKVIEW
        assert dict(restored.controls) == {"zoom_absolute": 150}

    def test_missing_fields_fall_back_to_defaults(self) -> None:
        profile = Profile.from_dict({})

        assert profile.tracking is False
        assert profile.mode is CameraMode.NORMAL
        assert dict(profile.controls) == {}

    @pytest.mark.parametrize(
        "data",
        [
            {"mode": "sideways"},
            {"controls": {"zoom_absolute": "wide"}},
            {"controls": ["zoom_absolute"]},
        ],
    )
    def test_invalid_data_raises_camera_error(self, data: dict[str, object]) -> None:
        with pytest.raises(CameraError, match="invalid"):
            Profile.from_dict(data)

    def test_describe(self) -> None:
        assert Profile(controls={"a": 1, "b": 2}).describe() == (
            "tracking off, normal mode, 2 picture and position settings"
        )
        assert Profile(tracking=True).describe().startswith("tracking on")
