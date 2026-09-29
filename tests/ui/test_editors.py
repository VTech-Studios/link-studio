import pytest
from PySide6.QtWidgets import QCheckBox, QComboBox, QSlider, QSpinBox
from pytestqt.qtbot import QtBot

from link_studio.domain import Control, ControlKind
from link_studio.ui.editors import (
    SLIDER_DEBOUNCE_MS,
    BooleanEditor,
    ControlEditor,
    IntegerEditor,
    MenuEditor,
    create_editor,
)
from tests.fakes import integer

PAN = integer("pan_absolute", 0, minimum=-522000, maximum=522000, step=3600, default=0)
POWER = Control("power_line_frequency", ControlKind.MENU, maximum=2, value=1).with_menu(
    {0: "Disabled", 1: "50 Hz", 2: "60 Hz"}
)
AUTO = Control("white_balance_automatic", ControlKind.BOOLEAN, value=1)


def record(editor: BooleanEditor | MenuEditor | IntegerEditor) -> list[int]:
    values: list[int] = []
    editor.edited.connect(values.append)
    return values


def test_factory_picks_the_editor_for_each_kind(qtbot: QtBot) -> None:
    assert isinstance(create_editor(PAN), IntegerEditor)
    assert isinstance(create_editor(POWER), MenuEditor)
    assert isinstance(create_editor(AUTO), BooleanEditor)


class TestIntegerEditor:
    def test_slider_drag_sends_one_snapped_value_after_the_pause(self, qtbot: QtBot) -> None:
        editor = IntegerEditor(PAN)
        qtbot.addWidget(editor)
        values = record(editor)
        slider = editor.findChild(QSlider)
        assert slider is not None

        for position in (1000, 2000, 5000):
            slider.setValue(position)
        assert values == []

        qtbot.waitUntil(lambda: values == [3600], timeout=SLIDER_DEBOUNCE_MS * 10)
        spin = editor.findChild(QSpinBox)
        assert spin is not None
        assert spin.value() == 3600

    def test_spin_box_sends_its_value_when_editing_finishes(self, qtbot: QtBot) -> None:
        editor = IntegerEditor(PAN)
        qtbot.addWidget(editor)
        values = record(editor)
        spin = editor.findChild(QSpinBox)
        assert spin is not None

        spin.setValue(-36000)
        spin.editingFinished.emit()

        assert values == [-36000]

    def test_display_does_not_echo_back(self, qtbot: QtBot) -> None:
        editor = IntegerEditor(PAN)
        qtbot.addWidget(editor)
        values = record(editor)

        editor.display(integer("pan_absolute", 72000, minimum=-522000, maximum=522000, step=3600))
        qtbot.wait(SLIDER_DEBOUNCE_MS * 2)

        assert values == []
        slider = editor.findChild(QSlider)
        assert slider is not None
        assert slider.value() == 72000


class TestBooleanEditor:
    def test_toggle_sends_value_and_display_does_not(self, qtbot: QtBot) -> None:
        editor = BooleanEditor(AUTO)
        qtbot.addWidget(editor)
        values = record(editor)
        box = editor.findChild(QCheckBox)
        assert box is not None

        editor.display(AUTO)
        box.setChecked(False)

        assert values == [0]


class TestMenuEditor:
    def test_lists_entries_and_sends_the_chosen_value(self, qtbot: QtBot) -> None:
        editor = MenuEditor(POWER)
        qtbot.addWidget(editor)
        values = record(editor)
        combo = editor.findChild(QComboBox)
        assert combo is not None

        editor.display(POWER)
        assert combo.currentText() == "50 Hz"

        combo.activated.emit(2)

        assert [combo.itemText(i) for i in range(combo.count())] == ["Disabled", "50 Hz", "60 Hz"]
        assert values == [2]

    def test_value_missing_from_the_menu_keeps_the_selection(self, qtbot: QtBot) -> None:
        editor = MenuEditor(POWER)
        qtbot.addWidget(editor)
        combo = editor.findChild(QComboBox)
        assert combo is not None

        editor.display(POWER)
        editor.display(Control("power_line_frequency", ControlKind.MENU, value=7))

        assert combo.currentText() == "50 Hz"


def test_base_editor_requires_display(qtbot: QtBot) -> None:
    editor = ControlEditor(AUTO)
    qtbot.addWidget(editor)

    with pytest.raises(NotImplementedError):
        editor.display(AUTO)
