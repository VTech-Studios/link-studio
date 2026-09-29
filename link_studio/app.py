"""Command-line entry point: the GUI by default, or `--apply` for systemd."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .config import Config
from .infrastructure.process import SubprocessRunner
from .ports import CommandRunner
from .services.on_connect import DEFAULT_TIMING, ApplyOnConnect, Timing
from .wiring import build_locator, build_services


def run_apply(config: Config, runner: CommandRunner, timing: Timing = DEFAULT_TIMING) -> int:
    apply = ApplyOnConnect(
        locator=build_locator(config),
        service_for=lambda device: build_services(config, device, runner).startup,
        report=lambda message: print(message, file=sys.stderr),
        timing=timing,
    )
    return apply.run()


def run_gui(config: Config, runner: CommandRunner) -> int:
    """Start the graphical interface.

    Qt is imported here rather than at module level so that `--apply`, which
    systemd runs at every camera connect, never loads it. That keeps the
    headless path fast and able to run before a desktop session exists.
    """
    from .ui.application import run

    return run(config, runner)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="link-studio", description="Control panel for the Insta360 Link 2.")
    parser.add_argument("--apply", action="store_true", help="apply the saved startup settings and exit")
    args = parser.parse_args(argv)

    config = Config.from_environment()
    runner = SubprocessRunner()
    return run_apply(config, runner) if args.apply else run_gui(config, runner)
