import json
from pathlib import Path

import pytest

from link_studio.domain import CameraError, CameraMode, Profile
from link_studio.infrastructure.profile_store import JsonProfileStore


def test_missing_file_means_nothing_saved(tmp_path: Path) -> None:
    assert JsonProfileStore(tmp_path / "startup.json").load() is None


def test_round_trip_creates_parent_directories(tmp_path: Path) -> None:
    store = JsonProfileStore(tmp_path / "link-studio" / "startup.json")
    profile = Profile(tracking=False, mode=CameraMode.WHITEBOARD, controls={"brightness": 60})

    store.save(profile)

    assert store.load() == Profile.from_dict(profile.to_dict())


def test_save_leaves_no_temporary_file(tmp_path: Path) -> None:
    JsonProfileStore(tmp_path / "startup.json").save(Profile())

    assert [p.name for p in tmp_path.iterdir()] == ["startup.json"]


def test_writes_readable_json(tmp_path: Path) -> None:
    path = tmp_path / "startup.json"

    JsonProfileStore(path).save(Profile(controls={"zoom_absolute": 120}))

    assert json.loads(path.read_text()) == {
        "tracking": False,
        "mode": "normal",
        "controls": {"zoom_absolute": 120},
    }


def test_corrupt_json_raises_camera_error(tmp_path: Path) -> None:
    path = tmp_path / "startup.json"
    path.write_text("{not json")

    with pytest.raises(CameraError, match="not valid JSON"):
        JsonProfileStore(path).load()


def test_invalid_profile_raises_camera_error(tmp_path: Path) -> None:
    path = tmp_path / "startup.json"
    path.write_text('{"mode": "sideways"}')

    with pytest.raises(CameraError, match="invalid"):
        JsonProfileStore(path).load()


def test_unreadable_path_raises_camera_error(tmp_path: Path) -> None:
    with pytest.raises(CameraError, match="Could not read"):
        JsonProfileStore(tmp_path).load()


def test_location(tmp_path: Path) -> None:
    assert JsonProfileStore(tmp_path / "a.json").location == str(tmp_path / "a.json")
