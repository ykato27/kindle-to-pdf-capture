"""Screenshot loop that turns Kindle pages until the book ends."""

from __future__ import annotations

import subprocess
import sys
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image

from . import frames
from .config import CaptureConfig

# 直近に保存したこの枚数のページのどれかと同じ画面を「進まなかった」とみなす。
# 2枚にするのは、ツールバーの表示・非表示が交互に切り替わる場合にも止まるため
RECENT_PAGES = 2
# ページが進まなかった回数がこれだけ続いたら本の終わりとみなす（同じ画面が3枚続いた状態）
STALL_LIMIT = 2

KINDLE_APP_NAME = "Amazon Kindle"


@dataclass
class CaptureResult:
    pages: list[Path]
    reason: str  # "end_of_book" / "max_pages" / "stopped" / "focus_lost"


def prepare_folder(images_dir: Path) -> None:
    """Create the target directory and remove images left by a previous run."""

    images_dir.mkdir(parents=True, exist_ok=True)
    for path in images_dir.glob("page_*.png"):
        path.unlink(missing_ok=True)


def capture_book(
    config: CaptureConfig,
    screenshot: Callable[[], Image.Image],
    turn_page: Callable[[], None],
    stop: threading.Event,
    kindle_in_front: Callable[[], bool] = lambda: True,
) -> CaptureResult:
    """Capture pages until the screen stops changing, the page limit, or `stop`.

    Every screenshot and page turn first checks `kindle_in_front`, so that a
    switch to another app never sends keys to it or saves its screen as a page.

    A frame that matches a recently saved page is saved provisionally: it may
    be a real page that looks almost the same (a blank page, a short title).
    Only when STALL_LIMIT such frames come in a row are they deleted and the
    book treated as finished.
    """

    pages: list[Path] = []
    stalled: list[Path] = []
    recent: deque[Image.Image] = deque(maxlen=RECENT_PAGES)

    def seen_recently(fingerprint: Image.Image) -> bool:
        return any(frames.is_same_page(fingerprint, page) for page in recent)

    while not stop.is_set():
        if not kindle_in_front():
            return CaptureResult(pages, "focus_lost")
        image = screenshot()
        fingerprint = frames.fingerprint(image)
        if seen_recently(fingerprint):
            # 描画が遅れているだけかもしれないので、もう一度待って撮り直す
            if stop.wait(config.page_change_interval):
                break
            if not kindle_in_front():
                return CaptureResult(pages, "focus_lost")
            image = screenshot()
            fingerprint = frames.fingerprint(image)
        if stop.is_set():
            break  # 停止キーで画面が切り替わった後の1枚は保存しない

        path = config.images_dir / f"page_{len(pages) + 1:04d}.png"
        image.convert("RGB").save(path)
        pages.append(path)

        if seen_recently(fingerprint):
            stalled.append(path)
            print(f"ページが進んでいません（{len(stalled)}/{STALL_LIMIT}）: {path.name}")
            if len(stalled) >= STALL_LIMIT:
                for duplicate in stalled:
                    duplicate.unlink(missing_ok=True)
                    pages.remove(duplicate)
                return CaptureResult(pages, "end_of_book")
        else:
            stalled.clear()
            recent.append(fingerprint)
            print(f"撮影 {len(pages)}/{config.max_pages}: {path.name}")

        if len(pages) >= config.max_pages:
            return CaptureResult(pages, "max_pages")
        if stop.wait(config.capture_interval):
            break
        if not kindle_in_front():
            return CaptureResult(pages, "focus_lost")
        turn_page()
        if stop.wait(config.page_change_interval):
            break

    return CaptureResult(pages, "stopped")


def activate_kindle() -> None:
    """Bring Kindle for Mac to the front so that key presses reach it."""

    if sys.platform != "darwin":
        return
    result = subprocess.run(
        ["open", "-a", KINDLE_APP_NAME], capture_output=True, check=False
    )
    if result.returncode != 0:
        print(f"{KINDLE_APP_NAME} を前面に出せませんでした。手動で Kindle を前面にしてください。")


def kindle_is_front() -> bool:
    """Whether Kindle for Mac is the frontmost app (always True on other platforms)."""

    if sys.platform != "darwin":
        return True
    front = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True).stdout.strip()
    info = subprocess.run(
        ["lsappinfo", "info", "-only", "name", front], capture_output=True, text=True
    ).stdout
    return '"Kindle"' in info


def make_page_turner(navigation: str, direction: str) -> Callable[[], None]:
    import pyautogui

    if navigation == "key":
        return lambda: pyautogui.press(direction)

    # 本文の上をクリックするとツールバーの表示切り替えや文字の選択になるため、画面の端を押す
    width, height = pyautogui.size()
    x = round(width * (0.97 if direction == "right" else 0.03))
    y = height // 2
    return lambda: pyautogui.click(x, y)


def run(config: CaptureConfig, stop: threading.Event, countdown: int = 3) -> CaptureResult:
    """Capture with the real screen, keyboard and mouse.

    Moving the mouse to a screen corner (pyautogui's fail-safe) or Ctrl+C
    also stops the capture; the pages taken so far are kept.
    """

    import pyautogui

    pyautogui.FAILSAFE = True
    prepare_folder(config.images_dir)
    turn_page = make_page_turner(config.navigation, config.direction)

    activate_kindle()
    print("Kindle で最初のページを表示しておいてください。Esc キーで撮影を止められます。")
    for remaining in range(countdown, 0, -1):
        print(f"{remaining} 秒後に撮影を始めます...")
        if stop.wait(1):
            return CaptureResult([], "stopped")

    result = CaptureResult([], "stopped")
    try:
        result = capture_book(config, pyautogui.screenshot, turn_page, stop, kindle_is_front)
    except (KeyboardInterrupt, pyautogui.FailSafeException):
        result = CaptureResult(sorted(config.images_dir.glob("page_*.png")), "stopped")
    return result
