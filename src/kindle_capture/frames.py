"""Decide whether two screenshots show the same page.

Screenshots are never byte-identical to rely on a file hash, so frames are
compared as small grayscale images with a per-pixel tolerance.

The thresholds were measured on real Kindle for Mac screenshots and on
synthetic Japanese text pages (3456x2234, compared at FINGERPRINT_WIDTH=432):

- two different text pages: about 9% of pixels change
- a blank page followed by a chapter title page: about 0.13%
- the same page with the mouse hovering the page-turn arrow: 0.00-0.01%
- the same page with a "copied" toast or selection menu: 0.2-0.7%

A chapter title page differs from a blank page by less than UI noise does, so
the threshold is kept strict. Page turns by arrow keys produce no UI noise.
"""

from __future__ import annotations

from PIL import Image, ImageChops

FINGERPRINT_WIDTH = 432
PIXEL_TOLERANCE = 48  # 輝度の差がこれ以下の画素は変化なしとみなす（0-255）
SAME_PAGE_RATIO = 0.0005  # 変化した画素がこの割合未満なら同じページ（0.05%）

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
