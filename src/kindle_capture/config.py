"""Configuration helpers for Kindle capture sessions."""

from __future__ import annotations

import re
from pathlib import Path


PAGE_KEY_CHOICES = {
    "R": "right",
    "L": "left",
    "P": "pagedown",
}


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    response = input(f"{text}{suffix}: ").strip()
    return response or (default or "")


_INVALID_FS_CHARS = re.compile(r"[\\/:*?\"<>|]")


def _sanitize_book_name(book_name: str) -> str:
    sanitized = _INVALID_FS_CHARS.sub("_", "_".join(book_name.split()))
    return sanitized or "book"


def get_config_from_user() -> dict:
    """Collect configuration interactively from the user.

    Returns a dictionary containing all configuration values required by the
    capture and PDF generation routines.
    """

    book_name = _prompt("Enter book name", default="MyBook")

    total_pages_input = _prompt("How many pages to capture?", default="1")
    while not total_pages_input.isdigit() or int(total_pages_input) <= 0:
        print("Please enter a positive integer for the page count.")
        total_pages_input = _prompt("How many pages to capture?", default="1")
    total_pages = int(total_pages_input)

    print("Select page navigation key: R (Right Arrow), L (Left Arrow), P (PageDown)")
    page_key_choice = _prompt("Choose navigation key", default="R").upper()
    while page_key_choice not in PAGE_KEY_CHOICES:
        print("Invalid choice. Please select R, L, or P.")
        page_key_choice = _prompt("Choose navigation key", default="R").upper()
    page_key = PAGE_KEY_CHOICES[page_key_choice]

    capture_interval_input = _prompt(
        "Delay after screenshot in seconds (>=0)", default="0.5"
    )
    page_change_interval_input = _prompt(
        "Delay after page change in seconds (>=0)", default="1.0"
    )
    capture_interval = _parse_non_negative_float(capture_interval_input, 0.5)
    page_change_interval = _parse_non_negative_float(page_change_interval_input, 1.0)

    base_output = Path.home() / "kindle_capture"
    book_dir = base_output / _sanitize_book_name(book_name)
    images_dir = book_dir / "images"
    output_pdf = book_dir / f"{_sanitize_book_name(book_name)}.pdf"

    return {
        "book_name": book_name,
        "total_pages": total_pages,
        "page_key": page_key,
        "images_dir": images_dir,
        "output_pdf": output_pdf,
        "capture_interval": capture_interval,
        "page_change_interval": page_change_interval,
    }


def _parse_non_negative_float(value: str, fallback: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed >= 0 else fallback
    except ValueError:
        return fallback
