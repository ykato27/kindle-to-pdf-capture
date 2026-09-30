"""Combine captured images into a single, reasonably small PDF.

Each page is shrunk and JPEG-compressed, then embedded as is. The file is
written in one pass with only one page in memory at a time; Pillow's own PDF
writer keeps every page in memory, and its append mode rewrites the page list
on every page, so its size and time grow faster than the page count.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from .config import PdfQuality


def _page_jpeg(path: Path, quality: PdfQuality) -> tuple[bytes, int, int]:
    try:
        with Image.open(path) as image:
            page = image.convert("RGB")
    except OSError as exc:
        raise OSError(f"{path.name} を読めません（{exc}）") from exc
    if quality.max_height is not None and page.height > quality.max_height:
        width = max(1, round(page.width * quality.max_height / page.height))
        page = page.resize((width, quality.max_height), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    page.save(buffer, "JPEG", quality=quality.jpeg_quality)
    return buffer.getvalue(), page.width, page.height


class _PdfWriter:
    """Writes numbered PDF objects and remembers their byte offsets for the xref table."""

    def __init__(self, file: BinaryIO) -> None:
        self.file = file
        self.position = 0
        self.offsets: dict[int, int] = {}

    def write(self, data: bytes) -> None:
        self.file.write(data)
        self.position += len(data)

    def object(self, number: int, dictionary: str, stream: bytes | None = None) -> None:
        self.offsets[number] = self.position
        self.write(f"{number} 0 obj\n{dictionary}".encode("ascii"))
        if stream is not None:
            self.write(b"\nstream\n" + stream + b"\nendstream")
        self.write(b"\nendobj\n")

    def finish(self, root: int) -> None:
        size = max(self.offsets) + 1
        xref = self.position
        rows = [b"0000000000 65535 f \n"]
        rows += [f"{self.offsets[number]:010d} 00000 n \n".encode("ascii") for number in range(1, size)]
        self.write(f"xref\n0 {size}\n".encode("ascii") + b"".join(rows))
        self.write(
            f"trailer\n<< /Size {size} /Root {root} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
        )


def images_to_pdf(image_paths: list[Path], output_pdf: Path, quality: PdfQuality) -> Path:
    """Write the images as PDF pages (1 pixel = 1 point)."""

    if not image_paths:
        raise FileNotFoundError("PDF にする画像がありません。")

    print(f"PDF を作成しています（{len(image_paths)} ページ）...")
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_pdf.with_suffix(".pdf.tmp")
    try:
        _write(image_paths, tmp, quality)
    except BaseException:
        tmp.unlink(missing_ok=True)  # 途中で止まったら書きかけのファイルを残さない
        raise
    tmp.replace(output_pdf)
    print(f"PDF を保存しました（{len(image_paths)} ページ）: {output_pdf}")
    return output_pdf


def _write(image_paths: list[Path], tmp: Path, quality: PdfQuality) -> None:
    # 番号は 1=カタログ、2=ページ一覧、以降はページごとに 画像・描画命令・ページ の3つ
    page_numbers = []
    with open(tmp, "wb") as file:
        writer = _PdfWriter(file)
        writer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        for index, path in enumerate(image_paths):
            jpeg, width, height = _page_jpeg(path, quality)
            image_no, content_no, page_no = 3 + 3 * index, 4 + 3 * index, 5 + 3 * index
            writer.object(
                image_no,
                f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} "
                f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(jpeg)} >>",
                jpeg,
            )
            content = f"q {width} 0 0 {height} 0 0 cm /Im0 Do Q".encode("ascii")
            writer.object(content_no, f"<< /Length {len(content)} >>", content)
            writer.object(
                page_no,
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /XObject << /Im0 {image_no} 0 R >> >> /Contents {content_no} 0 R >>",
            )
            page_numbers.append(page_no)
        kids = " ".join(f"{number} 0 R" for number in page_numbers)
        writer.object(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>")
        writer.object(1, "<< /Type /Catalog /Pages 2 0 R >>")
        writer.finish(root=1)
