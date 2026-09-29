from pathlib import Path

from link_studio.config import LOOPBACK_DEVICE, Config


def test_uses_xdg_config_home() -> None:
    config = Config.from_environment(
        {"HOME": "/home/u", "XDG_CONFIG_HOME": "/cfg"}, python="/usr/bin/python3"
    )

    assert config.profile_path == Path("/cfg/link-studio/startup.json")
    assert config.systemd_user_dir == Path("/cfg/systemd/user")


def test_falls_back_to_home_dot_config() -> None:
    config = Config.from_environment({"HOME": "/home/u"}, python="/usr/bin/python3")

    assert config.config_dir == Path("/home/u/.config/link-studio")


def test_camera_name_is_overridable() -> None:
    assert Config.from_environment({"HOME": "/h"}).camera_name == "Insta360"
    assert Config.from_environment({"HOME": "/h", "LINK_STUDIO_CAMERA": "Obsbot"}).camera_name == "Obsbot"


def test_apply_command_uses_the_given_interpreter_quoted() -> None:
    config = Config.from_environment({"HOME": "/h"}, python="/opt/my env/bin/python")

    assert config.apply_command == "'/opt/my env/bin/python' -m link_studio --apply"


def test_loopback_matches_cam_rotate() -> None:
    assert Config.from_environment({"HOME": "/h"}).loopback_device == LOOPBACK_DEVICE == Path("/dev/video10")
