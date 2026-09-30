from __future__ import annotations

import random
import threading
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from kindle_capture.config import CaptureConfig


def make_page(seed: int, size: tuple[int, int] = (864, 558)) -> Image.Image:
    """A screen with a white page on black margins and text-like lines."""

    rng = random.Random(seed)
    width, height = size
    image = Image.new("RGB", size, "black")
    draw = ImageDraw.Draw(image)
    left, right = width // 4, width * 3 // 4
    draw.rectangle((left, 0, right, height), fill="white")
    for y in range(20, height - 20, 14):
        x = left + 12
        while x < right - 20:
            word = rng.randint(4, 30)
            draw.rectangle((x, y, min(x + word, right - 12), y + 7), fill="black")
            x += word + rng.randint(4, 10)
    return image


class FakeScreen:
    """Kindle stand-in: `turn_page` advances through `pages`, then stays on the last one.

    `lag` screenshots right after a page turn still show the previous page.
    """

    def __init__(self, pages: list[Image.Image], lag: int = 0) -> None:
        self.pages = pages
        self.index = 0
        self.lag = lag
        self._stale = 0
        self.turns = 0

    def screenshot(self) -> Image.Image:
        if self._stale > 0:
            self._stale -= 1
            return self.pages[max(0, self.index - 1)].copy()
        return self.pages[self.index].copy()

    def turn_page(self) -> None:
        self.turns += 1
        if self.index < len(self.pages) - 1:
            self.index += 1
            self._stale = self.lag


def make_config(tmp_path: Path, **overrides) -> CaptureConfig:
    values = dict(
        book_name="test book",
        max_pages=100,
        direction="right",
        navigation="key",
        capture_interval=0,
        page_change_interval=0,
        output_root=tmp_path,
    )
    values.update(overrides)
    config = CaptureConfig(**values)
    config.images_dir.mkdir(parents=True)
    return config


@pytest.fixture
def stop() -> threading.Event:
    return threading.Event()
