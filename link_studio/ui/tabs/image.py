"""Image tab: every standard control that is not part of framing."""

from __future__ import annotations

from PySide6.QtWidgets import QScrollArea, QWidget

from ...domain import Control
from ..controls_model import ControlsModel
from ..controls_panel import ControlsPanel
from ..feedback import StatusFeedback
from ..layout import fill, group, note, page
from .framing import is_framing_control


def is_image_control(control: Control) -> bool:
    return not is_framing_control(control)


class ImageTab(QWidget):
    def __init__(self, model: ControlsModel, feedback: StatusFeedback) -> None:
        super().__init__()
        self.panel = ControlsPanel(model, feedback, is_image_control)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(
            page(
                group(
                    "Picture",
                    self.panel,
                    note(
                        "Greyed-out controls are overridden by an automatic setting, for example white "
                        "balance temperature while automatic white balance is on."
                    ),
                )
            )
        )
        fill(self, scroll)
