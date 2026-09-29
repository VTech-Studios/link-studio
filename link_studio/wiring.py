"""Composition root: the one place that chooses concrete implementations.

Everything else receives its collaborators through its constructor, so this
module is the only one that knows `v4l2-ctl`, `linkctl`, systemd and JSON
files are involved. Swapping any of them means changing this file alone.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from .config import Config
from .infrastructure.autostart import SystemdAutostart
from .infrastructure.discovery import SysfsCameraLocator
from .infrastructure.linkctl import LinkctlBackend
from .infrastructure.profile_store import JsonProfileStore
from .infrastructure.rotation import CamRotateService
from .infrastructure.v4l2 import V4l2ControlBackend
from .ports import Autostart, CameraLocator, CommandRunner, ControlBackend, RotationService
from .services.startup import StartupService


@dataclass(frozen=True)
class Services:
    """Everything that talks to one camera.

    The vendor backend is typed as the concrete adapter because it serves two
    ports, tracking and gimbal.
    """

    controls: ControlBackend
    vendor: LinkctlBackend
    startup: StartupService
    autostart: Autostart
    rotation: RotationService | None


def build_locator(config: Config) -> CameraLocator:
    return SysfsCameraLocator(config.sysfs_video, config.camera_name, exclude=config.loopback_device)


def build_services(config: Config, device: str, runner: CommandRunner) -> Services:
    """Wire every adapter for one camera device.

    The rotation service is only offered when `cam-rotate` is installed, so
    its tab does not appear on machines that cannot use it.
    """
    controls = V4l2ControlBackend(runner, device)
    vendor = LinkctlBackend(runner, device)
    rotation = CamRotateService(runner, config.loopback_device) if shutil.which("cam-rotate") else None
    return Services(
        controls=controls,
        vendor=vendor,
        startup=StartupService(controls, vendor, JsonProfileStore(config.profile_path)),
        autostart=SystemdAutostart(runner, config.systemd_user_dir, config.camera_name, config.apply_command),
        rotation=rotation,
    )
