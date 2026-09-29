"""Finds the camera's capture node in sysfs."""

from __future__ import annotations

from pathlib import Path


class SysfsCameraLocator:
    """CameraLocator that matches video devices by name.

    A UVC camera registers two nodes: the picture, with sysfs index 0, and a
    metadata stream. Only index 0 can be controlled and captured. Matching
    by name rather than number survives replugging, which renumbers nodes.
    The loopback device is excluded because cam-rotate can give it a
    similar name, and returning it would point the app at its own output.
    """

    def __init__(self, sysfs_root: Path, name_fragment: str, exclude: Path | None = None) -> None:
        self._sysfs_root = sysfs_root
        self._name_fragment = name_fragment
        self._exclude = str(exclude) if exclude is not None else None

    def find(self) -> str | None:
        for node in sorted(self._sysfs_root.glob("video*")):
            device = f"/dev/{node.name}"
            if device != self._exclude and self._is_matching_capture_node(node):
                return device
        return None

    def _is_matching_capture_node(self, node: Path) -> bool:
        try:
            name = (node / "name").read_text()
            index = (node / "index").read_text().strip()
        except OSError:
            return False
        return self._name_fragment in name and index == "0"
