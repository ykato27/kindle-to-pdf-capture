"""Combine captured images into a single, reasonably small PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops

from .config import PdfQuality

_BOX_REDUCE = 8  # 余白の検出は 1/8 に縮めた画像で行う
_BACKGROUND_TOLERANCE = 16
_BACKGROUND_LUT = [0] * (_BACKGROUND_TOLERANCE + 1) + [255] * (255 - _BACKGROUND_TOLERANCE)

Box = tuple[int, int, int, int]


def _content_box(image: Image.Image) -> Box | None:
    """Area that differs from the screen background (the left edge color)."""

    small = image.convert("RGB").reduce(_BOX_REDUCE)
    background = Image.new("RGB", small.size, small.getpixel((0, small.height // 2)))
    mask = ImageChops.difference(small, background).convert("L").point(_BACKGROUND_LUT)
    box = mask.getbbox()
    if box is None:
        return None
    left, top, right, bottom = box
    # 縮小で端が切れないよう、1マス分広げて元の座標に戻す
    return (
        max(0, (left - 1) * _BOX_REDUCE),
        max(0, (top - 1) * _BOX_REDUCE),
        min(image.width, (right + 1) * _BOX_REDUCE),
        min(image.height, (bottom + 1) * _BOX_REDUCE),
    )


def common_content_box(image_paths: Iterable[Path]) -> Box | None:
    """Smallest box that keeps the content of every page, so all pages share one size."""

    union: Box | None = None
    for path in image_paths:
        with Image.open(path) as image:
            box = _content_box(image)
        if box is None:
            continue
        if union is None:
            union = box
        else:
            union = (
                min(union[0], box[0]),
                min(union[1], box[1]),
                max(union[2], box[2]),
                max(union[3], box[3]),
            )
    return union


def _prepare_page(image: Image.Image, box: Box | None, quality: PdfQuality) -> Image.Image:
    page = image.convert("RGB")
    if box is not None:
        page = page.crop(box)
    if quality.max_height is not None and page.height > quality.max_height:
        width = max(1, round(page.width * quality.max_height / page.height))
        page = page.resize((width, quality.max_height), Image.Resampling.LANCZOS)
    return page


def images_to_pdf(image_paths: list[Path], output_pdf: Path, quality: PdfQuality) -> Path:
    """Write the images as PDF pages, one page in memory at a time."""

    if not image_paths:
        raise FileNotFoundError("PDF にする画像がありません。")

    box = common_content_box(image_paths)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    for index, path in enumerate(image_paths):
        with Image.open(path) as image:
            page = _prepare_page(image, box, quality)
        page.save(output_pdf, "PDF", append=index > 0, quality=quality.jpeg_quality)
    print(f"PDF を保存しました（{len(image_paths)} ページ）: {output_pdf}")
    return output_pdf
