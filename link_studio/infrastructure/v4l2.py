"""Standard V4L2 controls through `v4l2-ctl`.

Controls are listed from the camera on every read rather than hard-coded, so
the GUI shows exactly what the connected camera and firmware offer.
"""

from __future__ import annotations

import re

from ..domain import Control, ControlKind
from ..ports import CommandRunner

_CONTROL_LINE = re.compile(r"^\s*(?P<name>\w+)\s+0x[0-9a-f]+\s+\((?P<kind>\w+)\)\s*:\s*(?P<fields>.*)$")
_MENU_LINE = re.compile(r"^\s*(?P<value>\d+):\s*(?P<text>.+)$")
_FIELD = re.compile(r"(\w+)=(\S+)")
_SUPPORTED_KINDS = frozenset(kind.value for kind in ControlKind)


def parse_controls(text: str) -> list[Control]:
    """Parse the output of `v4l2-ctl --list-ctrls-menus`.

    A control line looks like
    `brightness 0x00980900 (int) : min=0 max=100 step=1 default=50 value=50`,
    and a menu control is followed by indented `1: 50 Hz` entries. Kinds this
    application cannot edit (buttons, 64-bit integers, strings) are skipped
    along with their menu entries, so a new firmware control never breaks
    parsing.
    """
    controls: list[Control] = []
    menu: dict[int, str] | None = None

    for line in text.splitlines():
        if header := _CONTROL_LINE.match(line):
            _attach_menu(controls, menu)
            control = _parse_header(header)
            menu = {} if control is not None and control.kind is ControlKind.MENU else None
            if control is not None:
                controls.append(control)
        elif menu is not None and (item := _MENU_LINE.match(line)):
            menu[int(item["value"])] = item["text"].strip()

    _attach_menu(controls, menu)
    return controls


def _parse_header(header: re.Match[str]) -> Control | None:
    if header["kind"] not in _SUPPORTED_KINDS:
        return None
    fields = dict(_FIELD.findall(header["fields"]))
    return Control(
        name=header["name"],
        kind=ControlKind(header["kind"]),
        minimum=int(fields.get("min", 0)),
        maximum=int(fields.get("max", 1)),
        step=int(fields.get("step", 1)),
        default=int(fields.get("default", 0)),
        value=int(fields.get("value", 0)),
        inactive="inactive" in fields.get("flags", ""),
    )


def _attach_menu(controls: list[Control], menu: dict[int, str] | None) -> None:
    if controls and menu is not None:
        controls[-1] = controls[-1].with_menu(menu)


class V4l2ControlBackend:
    """ControlBackend for one video device."""

    def __init__(self, runner: CommandRunner, device: str) -> None:
        self._runner = runner
        self._device = device

    def list_controls(self) -> list[Control]:
        return parse_controls(self._runner.run(["v4l2-ctl", "-d", self._device, "--list-ctrls-menus"]))

    def set_control(self, name: str, value: int) -> None:
        self._runner.run(["v4l2-ctl", "-d", self._device, "-c", f"{name}={value}"])
