"""Parser tests against output captured from a real Insta360 Link 2.

The sample is kept byte for byte as v4l2-ctl printed it, including its long
lines and tab indentation, because the parser has to cope with exactly that.
"""

from link_studio.domain import ControlKind
from link_studio.infrastructure.v4l2 import V4l2ControlBackend, parse_controls
from tests.fakes import FakeRunner

LINK_2_OUTPUT = """
User Controls

                     brightness 0x00980900 (int)    : min=0 max=100 step=1 default=50 value=50 flags=has-min-max
        white_balance_automatic 0x0098090c (bool)   : default=1 value=1
           power_line_frequency 0x00980918 (menu)   : min=0 max=2 default=3 value=1 (50 Hz)
				0: Disabled
				1: 50 Hz
				2: 60 Hz
      white_balance_temperature 0x0098091a (int)    : min=2000 max=10000 step=1 default=6400 value=3227 flags=inactive, has-min-max

Camera Controls

                   pan_absolute 0x009a0908 (int)    : min=-522000 max=522000 step=3600 default=0 value=-30600 flags=has-min-max
"""


def test_parses_every_supported_control() -> None:
    names = [c.name for c in parse_controls(LINK_2_OUTPUT)]

    assert names == [
        "brightness",
        "white_balance_automatic",
        "power_line_frequency",
        "white_balance_temperature",
        "pan_absolute",
    ]


def test_parses_integer_fields() -> None:
    pan = parse_controls(LINK_2_OUTPUT)[-1]

    assert pan.kind is ControlKind.INTEGER
    assert (pan.minimum, pan.maximum, pan.step, pan.default, pan.value) == (-522000, 522000, 3600, 0, -30600)
    assert not pan.inactive


def test_boolean_without_range_gets_zero_to_one() -> None:
    auto = parse_controls(LINK_2_OUTPUT)[1]

    assert auto.kind is ControlKind.BOOLEAN
    assert (auto.minimum, auto.maximum, auto.value) == (0, 1, 1)


def test_menu_entries_attach_to_their_control() -> None:
    power = parse_controls(LINK_2_OUTPUT)[2]

    assert power.kind is ControlKind.MENU
    assert power.value == 1
    assert dict(power.menu) == {0: "Disabled", 1: "50 Hz", 2: "60 Hz"}


def test_inactive_flag() -> None:
    temperature = parse_controls(LINK_2_OUTPUT)[3]

    assert temperature.inactive


def test_unsupported_kinds_are_skipped_with_their_menus() -> None:
    text = """
             exposure_metering 0x009a0919 (intmenu) : min=0 max=1 default=0 value=0
				0: 1
				1: 2
                    brightness 0x00980900 (int)    : min=0 max=100 step=1 default=50 value=50
    """

    controls = parse_controls(text)

    assert [c.name for c in controls] == ["brightness"]
    assert dict(controls[0].menu) == {}


def test_empty_output_gives_no_controls() -> None:
    assert parse_controls("") == []


def test_backend_lists_controls_for_its_device() -> None:
    runner = FakeRunner([(["v4l2-ctl"], LINK_2_OUTPUT)])

    controls = V4l2ControlBackend(runner, "/dev/video3").list_controls()

    assert len(controls) == 5
    assert runner.calls == [["v4l2-ctl", "-d", "/dev/video3", "--list-ctrls-menus"]]


def test_backend_sets_one_control() -> None:
    runner = FakeRunner()

    V4l2ControlBackend(runner, "/dev/video3").set_control("zoom_absolute", 150)

    assert runner.calls == [["v4l2-ctl", "-d", "/dev/video3", "-c", "zoom_absolute=150"]]
