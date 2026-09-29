"""Shared test setup.

Qt needs a display platform before any widget exists. The offscreen
platform lets the widget tests run headless, in CI or over SSH.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
