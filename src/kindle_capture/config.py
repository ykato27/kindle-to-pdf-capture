"""Configuration helpers for Kindle capture sessions."""

from __future__ import annotations

from pathlib import Path


PAGE_NAVIGATION_CHOICES = {
    "R": "click_right",
    "L": "click_left",
}


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    response = input(f"{text}{suffix}: ").strip()
    return response or (default or "")


def _sanitize_book_name(book_name: str) -> str:
    sanitized = "_".join(book_name.split())
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

    print("Select page navigation method: R (Click Right side), L (Click Left side)")
    page_nav_choice = _prompt("Choose navigation method", default="R").upper()
    while page_nav_choice not in PAGE_NAVIGATION_CHOICES:
        print("Invalid choice. Please select R or L.")
        page_nav_choice = _prompt("Choose navigation method", default="R").upper()
    page_navigation = PAGE_NAVIGATION_CHOICES[page_nav_choice]

    capture_interval_input = _prompt(
        "Delay after screenshot in seconds", default="0.5"
    )
    page_change_interval_input = _prompt(
        "Delay after page change in seconds", default="1.0"
    )
    try:
        capture_interval = float(capture_interval_input)
    except ValueError:
        capture_interval = 0.5
    try:
        page_change_interval = float(page_change_interval_input)
    except ValueError:
        page_change_interval = 1.0

    base_output = Path.home() / "kindle_capture"
    book_dir = base_output / _sanitize_book_name(book_name)
    images_dir = book_dir / "images"
    output_pdf = book_dir / f"{_sanitize_book_name(book_name)}.pdf"

    return {
        "book_name": book_name,
        "total_pages": total_pages,
        "page_navigation": page_navigation,
        "images_dir": images_dir,
        "output_pdf": output_pdf,
        "capture_interval": capture_interval,
        "page_change_interval": page_change_interval,
    }
