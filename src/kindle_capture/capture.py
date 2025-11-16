"""Screenshot capture routines for Kindle pages."""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Iterable


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


def prepare_folder(images_dir: Path) -> None:
    """Create the target directory and remove stale images."""

    images_dir.mkdir(parents=True, exist_ok=True)
    _remove_existing_images(images_dir)


def _countdown(seconds: int) -> None:
    for remaining in range(seconds, 0, -1):
        print(f"Starting capture in {remaining}...")
        time.sleep(1)


def capture_pages(config: dict) -> None:
    """Capture screenshots and advance Kindle pages."""

    pyautogui = _load_pyautogui()
    pyautogui.FAILSAFE = True

    images_dir: Path = config["images_dir"]
    total_pages: int = config["total_pages"]
    page_key: str = config["page_key"]
    capture_interval: float = config["capture_interval"]
    page_change_interval: float = config["page_change_interval"]

    print("Please focus the Kindle window and open the first page.")
    _countdown(3)

    for page_number in range(1, total_pages + 1):
        filename = images_dir / f"page_{page_number:04d}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        print(f"Captured page {page_number}/{total_pages}: {filename}")

        if page_number == total_pages:
            break

        time.sleep(capture_interval)
        pyautogui.press(page_key)
        time.sleep(page_change_interval)
