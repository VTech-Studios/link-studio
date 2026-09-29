"""Runs external commands and turns every failure into a CameraError."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

from ..domain import CameraError


class SubprocessRunner:
    """CommandRunner backed by `subprocess.run`."""

    def run(self, args: Sequence[str], timeout: float = 10.0) -> str:
        program = args[0]
        try:
            result = subprocess.run(list(args), capture_output=True, text=True, timeout=timeout, check=False)
        except FileNotFoundError:
            raise CameraError(f"{program} is not installed") from None
        except subprocess.TimeoutExpired:
            raise CameraError(f"{program} did not respond within {timeout:g} s") from None

        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise CameraError(detail or f"{program} exited with status {result.returncode}")
        return result.stdout
