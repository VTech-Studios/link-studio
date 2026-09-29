import sys

import pytest

from link_studio.domain import CameraError
from link_studio.infrastructure.process import SubprocessRunner

PYTHON = sys.executable


def test_returns_standard_output() -> None:
    assert SubprocessRunner().run([PYTHON, "-c", "print('hello')"]) == "hello\n"


def test_missing_program() -> None:
    with pytest.raises(CameraError, match="is not installed"):
        SubprocessRunner().run(["link-studio-no-such-program"])


def test_failure_reports_standard_error() -> None:
    script = "import sys; sys.stderr.write('device busy'); sys.exit(3)"

    with pytest.raises(CameraError, match="device busy"):
        SubprocessRunner().run([PYTHON, "-c", script])


def test_failure_without_output_reports_exit_status() -> None:
    with pytest.raises(CameraError, match="exited with status 4"):
        SubprocessRunner().run([PYTHON, "-c", "raise SystemExit(4)"])


def test_timeout() -> None:
    with pytest.raises(CameraError, match=r"did not respond within 0\.2 s"):
        SubprocessRunner().run([PYTHON, "-c", "import time; time.sleep(5)"], timeout=0.2)
