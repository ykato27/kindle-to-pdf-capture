"""Combine captured images into a single PDF."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Iterable

from .capture import _iter_image_files


def _load_pillow_image_module():
    if importlib.util.find_spec("PIL.Image") is None:
        raise RuntimeError(
            "Pillow is not installed. Please install dependencies with uv or pip."
        )
    return importlib.import_module("PIL.Image")


def _open_images(image_paths: Iterable[Path]):
    Image = _load_pillow_image_module()
    opened = []
    for path in image_paths:
        img = Image.open(path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        opened.append(img)
    return opened


def images_to_pdf(config: dict) -> Path:
    """Read captured images and write them into a single PDF."""

    images_dir: Path = config["images_dir"]
    output_pdf: Path = config["output_pdf"]

    image_files = list(_iter_image_files(images_dir))
    if not image_files:
        raise FileNotFoundError(
            f"No images found in {images_dir}. Please run capture before PDF export."
        )

    images = _open_images(image_files)
    first, *rest = images

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    first.save(output_pdf, "PDF", save_all=True, append_images=rest)
    print(f"Saved PDF to {output_pdf}")
    return output_pdf
