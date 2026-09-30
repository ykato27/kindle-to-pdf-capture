"""Talk to the Kindle app: bring it to the front, check focus, capture, turn pages.

On macOS the Kindle window itself is captured (screencapture -l), so other
windows, the menu bar clock or a second display never end up in a page.
Elsewhere the whole primary screen is captured with pyautogui.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

from PIL import Image

IS_MAC = sys.platform == "darwin"
APP_NAME = "Amazon Kindle"  # open -a に渡すアプリ名
OWNER_NAME = "Kindle"  # ウィンドウとプロセスの名前


def activate() -> None:
    """Bring Kindle for Mac to the front so that key presses reach it."""

    if not IS_MAC:
        return
    result = subprocess.run(["open", "-a", APP_NAME], capture_output=True, check=False)
    if result.returncode != 0:
        print(f"{APP_NAME} を前面に出せませんでした。手動で Kindle を前面にしてください。")


def is_front() -> bool:
    """Whether Kindle is the frontmost app (always True outside macOS)."""

    if not IS_MAC:
        return True
    front = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True).stdout.strip()
    info = subprocess.run(
        ["lsappinfo", "info", "-only", "name", front], capture_output=True, text=True
    ).stdout
    return f'"{OWNER_NAME}"' in info


def find_window() -> tuple[int, dict] | None:
    """(window id, bounds in points) of the largest visible Kindle window.

    In full screen the toolbar is a separate thin window, so it is skipped.
    """

    if not IS_MAC:
        return None
    import Quartz

    options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    windows = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID) or []
    candidates = [
        w
        for w in windows
        if w.get("kCGWindowOwnerName") == OWNER_NAME and w.get("kCGWindowLayer") == 0
    ]
    if not candidates:
        return None
    window = max(
        candidates, key=lambda w: w["kCGWindowBounds"]["Width"] * w["kCGWindowBounds"]["Height"]
    )
    return int(window["kCGWindowNumber"]), dict(window["kCGWindowBounds"])


def _capture_window(window_id: int) -> Image.Image:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "kindle.png"
        result = subprocess.run(
            ["screencapture", "-x", "-o", "-l", str(window_id), str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not path.exists():
            raise RuntimeError(f"Kindle のウィンドウを撮影できませんでした: {result.stderr.strip()}")
        with Image.open(path) as image:
            if "A" not in image.getbands():
                return image.convert("RGB")
            # ウィンドウ表示では角の丸い部分が透明になるので、黒ではなく白で埋める
            page = Image.new("RGB", image.size, "white")
            page.paste(image, mask=image.getchannel("A"))
            return page


def make_screenshotter(attempts: int = 6, interval: float = 0.5) -> Callable[[], Image.Image]:
    """Capture the Kindle window on macOS, the whole primary screen elsewhere.

    macOS never falls back to the whole screen: other windows would change
    every frame and the end of the book would never be detected.
    """

    if not IS_MAC:
        import pyautogui

        return lambda: pyautogui.screenshot().convert("RGB")

    for _ in range(attempts):
        if find_window() is not None:
            break
        time.sleep(interval)
    else:
        raise RuntimeError(
            "Kindle のウィンドウが画面上にありません。最小化や別のデスクトップになっていないか確かめてください。"
        )

    def capture_kindle_window() -> Image.Image:
        found = find_window()
        if found is None:
            raise RuntimeError("Kindle のウィンドウが見つからなくなりました。")
        return _capture_window(found[0])

    return capture_kindle_window


def make_page_turner(navigation: str, direction: str) -> Callable[[], None]:
    import pyautogui

    if navigation == "key":
        return lambda: pyautogui.press(direction)

    def click_edge() -> None:
        # 本文の上をクリックするとツールバーの表示切り替えや文字の選択になるため、端を押す
        found = find_window()
        if found is not None:
            bounds = found[1]
            left, top, width, height = bounds["X"], bounds["Y"], bounds["Width"], bounds["Height"]
        else:
            left, top = 0, 0
            width, height = pyautogui.size()
        x = left + width * (0.97 if direction == "right" else 0.03)
        pyautogui.click(round(x), round(top + height / 2))

    return click_edge


_PERMISSIONS = (  # (確認する関数, 求める関数, 表示名, 撮影に必須か)
    ("CGPreflightScreenCaptureAccess", "CGRequestScreenCaptureAccess", "画面収録", True),
    ("CGPreflightPostEventAccess", "CGRequestPostEventAccess", "アクセシビリティ", True),
    ("CGPreflightListenEventAccess", "CGRequestListenEventAccess", "入力監視", False),
)


def missing_permissions() -> tuple[list[str], list[str]]:
    """Missing macOS permissions: (needed to capture at all, needed only for Esc).

    For each missing one the system dialog is requested once, which also puts
    the terminal app into the list in System Settings.
    """

    if not IS_MAC:
        return [], []
    import Quartz

    required, optional = [], []
    for check_name, request_name, label, is_required in _PERMISSIONS:
        check = getattr(Quartz, check_name, None)
        if check is None or check():
            continue
        request = getattr(Quartz, request_name, None)
        if request is not None:
            request()
        (required if is_required else optional).append(label)
    return required, optional
