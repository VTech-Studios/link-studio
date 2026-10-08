"""Line icons drawn from SVG paths, so they follow the palette instead of the desktop theme."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

PATHS = {
    "framing": "M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3M2 12h20M12 2v20",
    "image": "M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6",
    "modes": "M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"
    "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
    "rotation": "M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5",
    "startup": "M12 2v10M18.4 6.6a9 9 0 1 1-12.8 0",
    "camera": "M16 10l5-3v10l-5-3zM5 6h9a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z",
    "refresh": "M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5",
}
RENDER_SCALE = 2


def pixmap(name: str, color: str, size: int) -> QPixmap:
    """Draw one icon at twice its size, so it stays sharp on high density screens."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{PATHS[name]}"/></svg>'
    )
    edge = size * RENDER_SCALE
    image = QPixmap(edge, edge)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    QSvgRenderer(QByteArray(svg.encode())).render(painter, QRectF(0, 0, edge, edge))
    painter.end()
    image.setDevicePixelRatio(RENDER_SCALE)
    return image


def icon(name: str, normal: str, active: str | None = None, size: int = 18) -> QIcon:
    """Build an icon that switches to `active` when its checkable button is checked."""
    result = QIcon()
    result.addPixmap(pixmap(name, normal, size), QIcon.Mode.Normal, QIcon.State.Off)
    result.addPixmap(pixmap(name, active or normal, size), QIcon.Mode.Normal, QIcon.State.On)
    return result
