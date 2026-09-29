from PySide6.QtWidgets import QLabel, QPushButton, QStatusBar
from pytestqt.qtbot import QtBot

from link_studio.domain import CameraError
from link_studio.ui.controls_model import ControlsModel
from link_studio.ui.controls_panel import ControlRow, ControlsPanel
from link_studio.ui.feedback import StatusFeedback
from tests.fakes import FakeControlBackend, integer


def make_panel(
    qtbot: QtBot, backend: FakeControlBackend, names: set[str] | None = None
) -> tuple[ControlsPanel, ControlsModel, QStatusBar]:
    model = ControlsModel(backend)
    model.refresh()
    status = QStatusBar()
    qtbot.addWidget(status)
    panel = ControlsPanel(
        model, StatusFeedback(status), lambda c: names is None or c.name in names, {"zoom_absolute": str}
    )
    qtbot.addWidget(panel)
    return panel, model, status


class TestControlsModel:
    def test_refresh_notifies_listeners(self, qtbot: QtBot) -> None:
        model = ControlsModel(FakeControlBackend([integer("brightness", 40)]))

        with qtbot.waitSignal(model.updated) as signal:
            model.refresh()

        assert [c.name for c in signal.args[0]] == ["brightness"]
        control = model.get("brightness")
        assert control is not None
        assert control.value == 40
        assert model.get("missing") is None

    def test_set_writes_then_rereads(self) -> None:
        backend = FakeControlBackend([integer("brightness", 40)])
        model = ControlsModel(backend)

        model.set("brightness", 70)

        assert backend.writes == [("brightness", 70)]
        control = model.get("brightness")
        assert control is not None
        assert control.value == 70


class TestControlsPanel:
    def test_builds_rows_only_for_included_controls(self, qtbot: QtBot) -> None:
        backend = FakeControlBackend([integer("brightness"), integer("zoom_absolute", 100)])

        panel, _, _ = make_panel(qtbot, backend, {"zoom_absolute"})

        assert list(panel.rows()) == ["zoom_absolute"]

    def test_edit_is_written_through_the_model(self, qtbot: QtBot) -> None:
        backend = FakeControlBackend([integer("brightness", 40)])
        panel, model, status = make_panel(qtbot, backend)

        panel.rows()["brightness"].changed.emit("brightness", 65)

        assert backend.writes == [("brightness", 65)]
        control = model.get("brightness")
        assert control is not None
        assert control.value == 65
        assert status.currentMessage() == "brightness = 65"

    def test_failed_write_is_reported_not_raised(self, qtbot: QtBot) -> None:
        backend = FakeControlBackend([integer("brightness")], failing={"brightness"})
        panel, _, status = make_panel(qtbot, backend)

        panel.rows()["brightness"].changed.emit("brightness", 1)

        assert status.currentMessage() == "Failed: brightness = 1: brightness refused"

    def test_rows_follow_model_updates(self, qtbot: QtBot) -> None:
        backend = FakeControlBackend([integer("brightness", 40)])
        panel, model, _ = make_panel(qtbot, backend)
        row = panel.rows()["brightness"]

        backend.set_control("brightness", 90)
        model.refresh()

        assert panel.rows()["brightness"] is row


class TestControlRow:
    def test_inactive_control_is_disabled(self, qtbot: QtBot) -> None:
        row = ControlRow(integer("white_balance_temperature", inactive=True))
        qtbot.addWidget(row)

        assert not row.isEnabled()

    def test_reset_sends_the_default(self, qtbot: QtBot) -> None:
        row = ControlRow(integer("brightness", 10, default=50))
        qtbot.addWidget(row)
        values: list[tuple[str, int]] = []
        row.changed.connect(lambda name, value: values.append((name, value)))
        reset = row.findChild(QPushButton)
        assert reset is not None

        reset.click()

        assert values == [("brightness", 50)]

    def test_reset_is_hidden_for_an_impossible_default(self, qtbot: QtBot) -> None:
        row = ControlRow(integer("power_line_frequency", 1, maximum=2, default=3))
        qtbot.addWidget(row)
        reset = row.findChild(QPushButton)
        assert reset is not None

        assert reset.isHidden()

    def test_readout_uses_the_formatter(self, qtbot: QtBot) -> None:
        row = ControlRow(integer("zoom_absolute", 150, maximum=400), lambda v: f"{v / 100:.1f}x")
        qtbot.addWidget(row)

        assert "1.5x" in [label.text() for label in row.findChildren(QLabel)]


class TestStatusFeedback:
    def test_success(self, qtbot: QtBot) -> None:
        status = QStatusBar()
        qtbot.addWidget(status)

        assert StatusFeedback(status).run("Done", lambda: None)
        assert status.currentMessage() == "Done"

    def test_camera_error_is_shown(self, qtbot: QtBot) -> None:
        status = QStatusBar()
        qtbot.addWidget(status)

        def fail() -> None:
            raise CameraError("device busy")

        assert not StatusFeedback(status).run("Start", fail)
        assert status.currentMessage() == "Failed: Start: device busy"
