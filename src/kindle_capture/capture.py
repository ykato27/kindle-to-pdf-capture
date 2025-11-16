"""Screenshot capture routines for Kindle pages."""

from __future__ import annotations

import hashlib
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


def _get_image_hash(image_path: Path) -> str:
    """Calculate hash of an image file."""
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _remove_duplicate_images(images_dir: Path, count: int) -> None:
    """Remove the last 'count' images from the directory."""
    image_files = list(_iter_image_files(images_dir))
    for img_file in image_files[-count:]:
        print(f"Removing duplicate image: {img_file}")
        img_file.unlink()


def capture_pages(config: dict) -> None:
    """Capture screenshots and advance Kindle pages."""

    pyautogui = _load_pyautogui()
    pyautogui.FAILSAFE = True

    images_dir: Path = config["images_dir"]
    total_pages: int = config["total_pages"]
    page_navigation: str = config["page_navigation"]
    capture_interval: float = config["capture_interval"]
    page_change_interval: float = config["page_change_interval"]

    print("Please focus the Kindle window and open the first page.")
    _countdown(3)

    # Get screen dimensions for click positioning
    screen_width, screen_height = pyautogui.size()

    # Determine click position based on navigation method
    if page_navigation == "click_right":
        click_x = int(screen_width * 0.9)  # 90% from left (right side)
    else:  # click_left
        click_x = int(screen_width * 0.1)  # 10% from left (left side)

    click_y = int(screen_height * 0.5)  # Middle of screen vertically

    # Track image hashes for duplicate detection
    recent_hashes: list[str] = []
    page_number = 0

    while page_number < total_pages:
        page_number += 1
        filename = images_dir / f"page_{page_number:04d}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        print(f"Captured page {page_number}/{total_pages}: {filename}")

        # Calculate hash for duplicate detection
        current_hash = _get_image_hash(filename)
        recent_hashes.append(current_hash)

        # Check for 3 consecutive duplicate images
        if len(recent_hashes) >= 3:
            last_three = recent_hashes[-3:]
            if len(set(last_three)) == 1:  # All 3 hashes are identical
                print("Detected 3 consecutive identical pages. Ending capture.")
                _remove_duplicate_images(images_dir, 2)  # Remove last 2 duplicates
                break

        if page_number >= total_pages:
            break

        time.sleep(capture_interval)
        pyautogui.click(click_x, click_y)
        time.sleep(page_change_interval)
