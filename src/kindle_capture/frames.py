"""Decide whether two screenshots show the same page.

Screenshots of an unchanged page are not always byte-identical, so frames are
compared as small grayscale images with a per-pixel tolerance.

Measured at FINGERPRINT_WIDTH=432 on real Kindle for Mac screenshots and on
synthetic Japanese pages (share of pixels that changed):

- two different text pages: 3-9%
- title page -> "this book is laid out horizontally" note (live): 0.19%
- blank page -> title page with a tiny heading such as "1" or "序章": 0.008-0.045%
- the same page after a key press at the end of the book (live): 0.00%
- the same page with the mouse hovering the page-turn arrow: 0.004%
- the same page with a "copied" toast or selection menu (click navigation): 0.2-0.7%

A page with a tiny heading differs from a blank page by less than UI noise
does, so only a near-exact match counts as the same page. Arrow keys and the
window-only capture produce no noise, so the end of the book still matches.
A too-strict threshold can only delay the stop; a loose one loses pages.
"""

from __future__ import annotations

from PIL import Image, ImageChops

FINGERPRINT_WIDTH = 432
PIXEL_TOLERANCE = 48  # 輝度の差がこれ以下の画素は変化なしとみなす（0-255）
SAME_PAGE_RATIO = 0.00002  # 変化した画素がこの割合未満なら同じページ（0.002%）

_CHANGED_LUT = [0] * (PIXEL_TOLERANCE + 1) + [255] * (255 - PIXEL_TOLERANCE)


def fingerprint(image: Image.Image) -> Image.Image:
    height = max(1, round(FINGERPRINT_WIDTH * image.height / image.width))
    return image.convert("L").resize((FINGERPRINT_WIDTH, height))


def changed_ratio(a: Image.Image, b: Image.Image) -> float:
    """Fraction of pixels that differ between two fingerprints."""

    if a.size != b.size:
        return 1.0
    changed = ImageChops.difference(a, b).point(_CHANGED_LUT).histogram()[255]
    return changed / (a.width * a.height)


def is_same_page(a: Image.Image, b: Image.Image) -> bool:
    return changed_ratio(a, b) < SAME_PAGE_RATIO
