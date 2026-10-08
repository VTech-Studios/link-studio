"""The window's colours and stylesheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Every colour the window uses, in one place.

    The window is always dark, like a video monitor, so the preview's
    picture is judged against a neutral surround rather than a bright
    desktop theme that would make it look darker than it is.
    """

    background: str = "#0d0f13"
    sidebar: str = "#111419"
    card: str = "#171b22"
    raised: str = "#1f242d"
    border: str = "#2a303b"
    text: str = "#e6e9ef"
    dim: str = "#8e97a6"
    faint: str = "#5d6676"
    accent: str = "#3b9eff"
    accent_hover: str = "#62b2ff"
    live: str = "#ef4444"


def stylesheet(palette: Palette) -> str:
    """Build the Qt stylesheet, which styles widgets by type and object name."""
    p = palette
    return f"""
    * {{ font-family: "Inter", "Noto Sans", "Cantarell", sans-serif; }}
    QWidget {{ color: {p.text}; font-size: 10pt; }}
    QMainWindow, #page, #pageBody {{ background: {p.background}; }}
    QToolTip {{ background: {p.raised}; color: {p.text}; border: 1px solid {p.border}; padding: 4px 8px; }}

    #sidebar {{ background: {p.sidebar}; border-right: 1px solid {p.border}; }}
    #brand {{ font-size: 14pt; font-weight: 700; }}
    #brandTag {{ color: {p.faint}; font-size: 8pt; font-weight: 600; letter-spacing: 2px; }}
    QPushButton#nav {{
        text-align: left; padding: 9px 12px; border: none; border-radius: 8px;
        color: {p.dim}; font-weight: 600; background: transparent;
    }}
    QPushButton#nav:hover {{ background: {p.card}; color: {p.text}; }}
    QPushButton#nav:checked {{ background: {p.raised}; color: {p.text}; }}
    #device {{ color: {p.dim}; font-size: 9pt; }}

    #title {{ font-size: 17pt; font-weight: 700; }}
    #subtitle, #note {{ color: {p.dim}; }}
    #note {{ font-size: 9pt; }}
    #section {{ color: {p.faint}; font-size: 8pt; font-weight: 700; letter-spacing: 2px; }}
    #card {{ background: {p.card}; border: 1px solid {p.border}; border-radius: 12px; }}

    #preview {{ background: {p.background}; }}
    #monitor {{ background: black; border: 1px solid {p.border}; border-radius: 12px; }}
    #idleTitle {{ font-size: 12pt; font-weight: 700; }}
    #liveBadge {{
        background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.55);
        border-radius: 9px; padding: 2px 10px; color: {p.live}; font-size: 8pt; font-weight: 700;
    }}

    QPushButton {{
        background: {p.raised}; border: 1px solid {p.border}; border-radius: 8px;
        padding: 6px 14px; font-weight: 600;
    }}
    QPushButton:hover {{ border-color: {p.accent}; }}
    QPushButton:pressed {{ background: {p.card}; }}
    QPushButton:disabled {{ color: {p.faint}; border-color: {p.border}; }}
    QPushButton#primary {{ background: {p.accent}; border: none; color: white; }}
    QPushButton#primary:hover {{ background: {p.accent_hover}; }}
    QPushButton#primary:checked {{ background: {p.raised}; border: 1px solid {p.live}; color: {p.live}; }}
    QPushButton#ghost {{ background: transparent; border: none; color: {p.faint}; padding: 4px 8px; }}
    QPushButton#ghost:hover {{ color: {p.text}; }}

    QComboBox, QSpinBox {{
        background: {p.raised}; border: 1px solid {p.border}; border-radius: 8px; padding: 5px 9px;
        selection-background-color: {p.accent};
    }}
    QComboBox:hover, QSpinBox:focus {{ border-color: {p.accent}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background: {p.raised}; border: 1px solid {p.border}; selection-background-color: {p.accent};
        outline: none; padding: 4px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}

    QSlider::groove:horizontal {{ height: 4px; background: {p.raised}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {p.accent}; border-radius: 2px; }}
    QSlider::sub-page:horizontal:disabled {{ background: {p.border}; }}
    QSlider::handle:horizontal {{
        background: white; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
    }}
    QSlider::handle:horizontal:disabled {{ background: {p.faint}; }}

    QCheckBox {{ spacing: 8px; }}
    QCheckBox:disabled {{ color: {p.faint}; }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 5px; border: 1px solid {p.border}; background: {p.raised};
    }}
    QCheckBox::indicator:checked {{ background: {p.accent}; border-color: {p.accent}; }}

    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
    QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 3px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {p.faint}; }}
    QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
        height: 0; background: none;
    }}

    QSplitter::handle {{ background: {p.border}; }}
    QStatusBar {{
        background: {p.sidebar}; border-top: 1px solid {p.border}; color: {p.dim}; padding-left: 8px;
    }}
    QStatusBar::item {{ border: none; }}
    """
