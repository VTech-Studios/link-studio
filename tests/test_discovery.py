from pathlib import Path

from link_studio.infrastructure.discovery import SysfsCameraLocator


def add_node(root: Path, node: str, name: str, index: int) -> None:
    directory = root / node
    directory.mkdir(parents=True)
    (directory / "name").write_text(f"{name}\n")
    (directory / "index").write_text(f"{index}\n")


def test_finds_the_capture_node_of_the_named_camera(tmp_path: Path) -> None:
    add_node(tmp_path, "video0", "Integrated Webcam", 0)
    add_node(tmp_path, "video2", "Insta360 Link 2: Insta360 Link", 1)
    add_node(tmp_path, "video3", "Insta360 Link 2: Insta360 Link", 0)

    assert SysfsCameraLocator(tmp_path, "Insta360").find() == "/dev/video3"


def test_skips_the_excluded_loopback_device(tmp_path: Path) -> None:
    add_node(tmp_path, "video10", "Insta360 rotated", 0)
    add_node(tmp_path, "video4", "Insta360 Link 2", 0)

    locator = SysfsCameraLocator(tmp_path, "Insta360", exclude=Path("/dev/video10"))

    assert locator.find() == "/dev/video4"


def test_returns_none_when_absent(tmp_path: Path) -> None:
    add_node(tmp_path, "video0", "Integrated Webcam", 0)

    assert SysfsCameraLocator(tmp_path, "Insta360").find() is None


def test_ignores_unreadable_nodes(tmp_path: Path) -> None:
    (tmp_path / "video0").mkdir()
    add_node(tmp_path, "video1", "Insta360 Link 2", 0)

    assert SysfsCameraLocator(tmp_path, "Insta360").find() == "/dev/video1"
