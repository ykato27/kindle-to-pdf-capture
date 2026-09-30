"""Screenshot loop that turns Kindle pages until the book ends."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image

from . import frames, kindle_app
from .config import CaptureConfig

# 直近に保存したこの枚数のページのどれかと同じ画面を「進まなかった」とみなす。
# 2枚にするのは、ツールバーの表示・非表示が交互に切り替わる場合にも止まるため
RECENT_PAGES = 2
# ページが進まなかった回数がこれだけ続いたら本の終わりとみなす（同じ画面が3枚続いた状態）
STALL_LIMIT = 2
# 同じ画面だったとき、描画の遅れを考えて撮り直す回数（間隔はページ送り後の待ち秒数）
RECHECKS = 3


@dataclass
class CaptureResult:
    pages: list[Path]
    reason: str  # "end_of_book" / "max_pages" / "stopped" / "focus_lost" / "error"


def list_pages(images_dir: Path) -> list[Path]:
    return sorted(images_dir.glob("page_*.png"))


def prepare_folder(images_dir: Path) -> None:
    """Create the target directory and remove images left by a previous run."""

    images_dir.mkdir(parents=True, exist_ok=True)
    for path in [*list_pages(images_dir), *images_dir.glob("page_*.tmp")]:
        path.unlink(missing_ok=True)


def _save(image: Image.Image, path: Path) -> None:
    # 保存の途中で止めても書きかけの PNG が残らないよう、別名で書いてから置き換える
    tmp = path.with_suffix(".tmp")
    image.convert("RGB").save(tmp, "PNG")
    tmp.replace(path)


def capture_book(
    config: CaptureConfig,
    screenshot: Callable[[], Image.Image],
    turn_page: Callable[[], None],
    stop: threading.Event,
    ready: Callable[[], bool] = lambda: True,
    stop_exceptions: tuple[type[BaseException], ...] = (),
) -> CaptureResult:
    """Capture pages until the screen stops changing, the page limit, or a stop.

    `ready` is checked before every screenshot and page turn; when it returns
    False (Kindle is no longer in front) the capture ends, so keys are never
    sent to another app. Exceptions in `stop_exceptions` and Ctrl+C end the
    capture like the Esc key does.

    A frame that matches a recently saved page is saved provisionally: it may
    be a real page that looks almost the same (a blank page, a short title).
    It is kept once a new page follows, and deleted when the capture ends on
    it, so the result never ends with repeated frames.
    """

    pages: list[Path] = []
    stalled: list[Path] = []
    recent: deque[Image.Image] = deque(maxlen=RECENT_PAGES)

    def seen_recently(fingerprint: Image.Image) -> bool:
        return any(frames.is_same_page(fingerprint, page) for page in recent)

    def finish(reason: str) -> CaptureResult:
        for duplicate in stalled:
            duplicate.unlink(missing_ok=True)
            pages.remove(duplicate)
        return CaptureResult(pages, reason)

    try:
        while not stop.is_set():
            if not ready():
                return finish("focus_lost")
            image = screenshot()
            fingerprint = frames.fingerprint(image)
            for _ in range(RECHECKS):
                if not seen_recently(fingerprint):
                    break
                # 描画が遅れているだけかもしれないので、待って撮り直す
                if stop.wait(config.page_change_interval):
                    return finish("stopped")
                if not ready():
                    return finish("focus_lost")
                image = screenshot()
                fingerprint = frames.fingerprint(image)
            if stop.is_set():
                break  # 停止した後に撮った1枚は保存しない

            seen = seen_recently(fingerprint)
            if not seen:
                stalled.clear()  # 新しいページが来たので、仮保存した分は本物のページとして残す
                if len(pages) >= config.max_pages:
                    return finish("max_pages")
            path = config.images_dir / f"page_{len(pages) + 1:04d}.png"
            _save(image, path)
            pages.append(path)

            if seen:
                stalled.append(path)
                print(f"ページが進んでいません（{len(stalled)}/{STALL_LIMIT}）: {path.name}")
                if len(stalled) >= STALL_LIMIT:
                    return finish("end_of_book")
            else:
                recent.append(fingerprint)
                print(f"撮影 {len(pages)}/{config.max_pages}: {path.name}")
                if len(pages) >= config.max_pages:
                    return finish("max_pages")

            if stop.wait(config.capture_interval):
                break
            if not ready():
                return finish("focus_lost")
            turn_page()
            if stop.wait(config.page_change_interval):
                break
    except (KeyboardInterrupt, *stop_exceptions):
        return finish("stopped")
    except Exception as exc:  # noqa: BLE001  撮れた分は PDF にするため、落とさずに返す
        print(f"撮影中にエラーが起きました: {exc}")
        return finish("error")

    return finish("stopped")


def run(config: CaptureConfig, stop: threading.Event, countdown: int = 3) -> CaptureResult:
    """Capture with the real Kindle window, keyboard and mouse.

    Moving the mouse to a screen corner (pyautogui's fail-safe) or Ctrl+C
    also stops the capture; the pages taken so far are kept.
    """

    import pyautogui

    pyautogui.FAILSAFE = True
    try:
        kindle_app.activate()
        print("Kindle で最初のページを表示しておいてください。Esc キーで撮影を止められます。")
        for remaining in range(countdown, 0, -1):
            print(f"{remaining} 秒後に撮影を始めます...")
            if stop.wait(1):
                return CaptureResult([], "stopped")
        screenshot = kindle_app.make_screenshotter()
    except KeyboardInterrupt:
        return CaptureResult([], "stopped")
    except RuntimeError as exc:
        print(exc)
        return CaptureResult([], "error")

    def ready() -> bool:
        pyautogui.failSafeCheck()  # マウスが画面の角にあれば FailSafeException で止まる
        return kindle_app.is_front()

    return capture_book(
        config,
        screenshot,
        kindle_app.make_page_turner(config.navigation, config.direction),
        stop,
        ready,
        stop_exceptions=(pyautogui.FailSafeException,),
    )
