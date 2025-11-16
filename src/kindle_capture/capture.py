"""Screenshot capture routines for Kindle pages."""

from __future__ import annotations

import hashlib
import importlib
import time
from pathlib import Path
from typing import Iterable

from PIL import Image


IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg")


def _load_pyautogui():
    if importlib.util.find_spec("pyautogui") is None:
        raise RuntimeError(
            "pyautogui is not installed. Please install dependencies with uv or pip."
        )
    return importlib.import_module("pyautogui")


def _remove_existing_images(images_dir: Path) -> None:
    for path in _iter_image_files(images_dir):
        path.unlink(missing_ok=True)


def _iter_image_files(images_dir: Path) -> Iterable[Path]:
    return sorted(
        (p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda p: p.name,
    )


def _hash_image(image: Image.Image) -> str:
    hasher = hashlib.md5()
    hasher.update(str(image.size).encode())
    hasher.update(image.mode.encode())
    hasher.update(image.tobytes())
    return hasher.hexdigest()


def prepare_folder(images_dir: Path) -> None:
    """Create the target directory and remove stale images."""

    images_dir.mkdir(parents=True, exist_ok=True)
    _remove_existing_images(images_dir)


def _countdown(seconds: int) -> None:
    for remaining in range(seconds, 0, -1):
        print(f"Starting capture in {remaining}...")
        time.sleep(1)


def _send_page_turn(pyautogui, page_key: str) -> None:
    """Send a reliable page turn keystroke."""

    pyautogui.keyDown(page_key)
    time.sleep(0.05)
    pyautogui.keyUp(page_key)


def capture_pages(config: dict) -> None:
    """Capture screenshots and advance Kindle pages."""

    pyautogui = _load_pyautogui()
    pyautogui.FAILSAFE = True

    images_dir: Path = config["images_dir"]
    total_pages: int = config["total_pages"]
    page_key: str = config["page_key"]
    capture_interval: float = config["capture_interval"]
    page_change_interval: float = config["page_change_interval"]

    print(
        "Please focus the Kindle window and open the first page. Move the mouse to"
        " the top-left corner to cancel at any time."
    )
    print(f"Screenshots will be saved under: {images_dir}")
    _countdown(3)

    last_hash: str | None = None
    duplicate_streak = 0
    captured_files: list[Path] = []

    for page_number in range(1, total_pages + 1):
        filename = images_dir / f"page_{page_number:04d}.png"
        screenshot = pyautogui.screenshot()
        screenshot_hash = _hash_image(screenshot)
        screenshot.save(filename)
        captured_files.append(filename)
        print(f"Captured page {page_number}/{total_pages}: {filename}")

        if screenshot_hash == last_hash:
            duplicate_streak += 1
        else:
            duplicate_streak = 1
            last_hash = screenshot_hash

        if duplicate_streak >= 3:
            for stale in captured_files[-2:]:
                stale.unlink(missing_ok=True)
            captured_files = captured_files[:-2]
            print("Detected identical screen three times in a row. Stopping capture and removing the last two duplicate images.")
            break

        if page_number == total_pages:
            break

        time.sleep(capture_interval)
        _send_page_turn(pyautogui, page_key)
        time.sleep(page_change_interval)
