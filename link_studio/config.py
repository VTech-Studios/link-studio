"""Application configuration, resolved once at start-up.

Every path and device name lives here instead of as a constant inside the
class that uses it, so the composition root hands each adapter exactly what
it needs and tests can point everything at temporary locations.
"""

from __future__ import annotations

import os
import shlex
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CAMERA_NAME = "Insta360"
LOOPBACK_DEVICE = Path("/dev/video10")
SYSFS_VIDEO = Path("/sys/class/video4linux")


@dataclass(frozen=True)
class Config:
    camera_name: str
    sysfs_video: Path
    loopback_device: Path
    config_dir: Path
    systemd_user_dir: Path
    apply_command: str

    @property
    def profile_path(self) -> Path:
        return self.config_dir / "startup.json"

    @classmethod
    def from_environment(cls, env: Mapping[str, str] = os.environ, python: str = sys.executable) -> Config:
        """Resolve configuration from the environment.

        The loopback device must match the one cam-rotate creates. The apply
        command uses the interpreter running now, which is the one this
        package is installed into, so the systemd unit works wherever the
        package was installed without hard-coding a path.
        """
        home = Path(env.get("HOME", str(Path.home())))
        xdg_config = Path(env.get("XDG_CONFIG_HOME", str(home / ".config")))
        return cls(
            camera_name=env.get("LINK_STUDIO_CAMERA", DEFAULT_CAMERA_NAME),
            sysfs_video=SYSFS_VIDEO,
            loopback_device=LOOPBACK_DEVICE,
            config_dir=xdg_config / "link-studio",
            systemd_user_dir=xdg_config / "systemd" / "user",
            apply_command=f"{shlex.quote(python)} -m link_studio --apply",
        )
