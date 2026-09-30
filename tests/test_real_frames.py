"""Replay screenshots from a real run where the page never turned.

The images are not part of the repository (they show a commercial book).
Point KINDLE_CAPTURE_REPLAY_DIR at such a folder to run this test.
"""

import os
from pathlib import Path

import pytest
from PIL import Image

from kindle_capture import capture

from conftest import FakeScreen, make_config

REPLAY_DIR = Path(os.environ.get("KINDLE_CAPTURE_REPLAY_DIR", "/nonexistent"))


@pytest.mark.skipif(not REPLAY_DIR.is_dir(), reason="set KINDLE_CAPTURE_REPLAY_DIR")
def test_stuck_kindle_run_stops_early(tmp_path, stop):
    frames = [Image.open(p).convert("RGB") for p in sorted(REPLAY_DIR.glob("page_*.png"))]
    config = make_config(tmp_path)
    screen = FakeScreen(frames)

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    print(f"{len(frames)} frames -> kept {len(result.pages)}, turns {screen.turns}")
    assert result.reason == "end_of_book"
    # 修正前の判定は57枚すべてを撮り続けた
    assert screen.turns < 10
