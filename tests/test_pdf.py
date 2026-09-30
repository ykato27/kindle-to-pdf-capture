import io

import pytest
from PIL import Image, PdfParser

from kindle_capture import pdf
from kindle_capture.config import QUALITIES, PdfQuality

from conftest import make_page


def read_pages(path):
    """(MediaBox size, image XObject, contents) for every page."""

    parser = PdfParser.PdfParser(str(path))
    try:
        pages = []
        for ref in parser.pages:
            page = parser.read_indirect(ref)
            image = parser.read_indirect(page[b"Resources"][b"XObject"][b"Im0"])
            contents = parser.read_indirect(page[b"Contents"])
            pages.append((tuple(page[b"MediaBox"][2:]), image, contents))
        return pages
    finally:
        parser.close()


def make_images(tmp_path, count, size=(1728, 1116)):
    paths = []
    for i in range(count):
        path = tmp_path / f"page_{i + 1:04d}.png"
        make_page(i, size=size).save(path)
        paths.append(path)
    return paths


def test_every_page_shows_its_jpeg_scaled_to_the_height_limit(tmp_path):
    paths = make_images(tmp_path, 3)

    output = pdf.images_to_pdf(paths, tmp_path / "book.pdf", PdfQuality(max_height=500, jpeg_quality=60))

    pages = read_pages(output)
    assert len(pages) == 3
    for size, image, contents in pages:
        assert size == (774, 500)
        assert image.dictionary[b"Subtype"] == b"Image"
        assert (image.dictionary[b"Width"], image.dictionary[b"Height"]) == size
        assert Image.open(io.BytesIO(image.buf)).format == "JPEG"
        assert b"/Im0 Do" in contents.buf
    assert not (tmp_path / "book.pdf.tmp").exists()


def test_high_quality_keeps_the_captured_size(tmp_path):
    paths = make_images(tmp_path, 1, size=(900, 600))

    output = pdf.images_to_pdf(paths, tmp_path / "book.pdf", QUALITIES["H"])

    assert [size for size, _, _ in read_pages(output)] == [(900, 600)]


def test_lighter_presets_make_smaller_files(tmp_path):
    paths = make_images(tmp_path, 3, size=(3456, 2234))
    sizes = {
        key: pdf.images_to_pdf(paths, tmp_path / f"{key}.pdf", QUALITIES[key]).stat().st_size
        for key in ("L", "S", "H")
    }
    assert sizes["L"] < sizes["S"] < sizes["H"]
    assert sizes["S"] < sizes["H"] / 2


def test_file_size_grows_in_proportion_to_page_count(tmp_path):
    # 1ページずつ追記する方式では、ページが増えるほど1ページあたりの容量が膨らんだ
    paths = make_images(tmp_path, 1) * 160
    quality = PdfQuality(max_height=200, jpeg_quality=60)
    small = pdf.images_to_pdf(paths[:20], tmp_path / "20.pdf", quality).stat().st_size
    large = pdf.images_to_pdf(paths, tmp_path / "160.pdf", quality).stat().st_size
    assert large / 160 < small / 20 * 1.02
    assert len(read_pages(tmp_path / "160.pdf")) == 160


def test_unreadable_image_names_the_file_and_leaves_no_partial_pdf(tmp_path):
    paths = make_images(tmp_path, 2)
    paths[1].write_bytes(b"")

    with pytest.raises(OSError, match="page_0002.png"):
        pdf.images_to_pdf(paths, tmp_path / "book.pdf", QUALITIES["S"])
    assert not (tmp_path / "book.pdf").exists()
    assert not (tmp_path / "book.pdf.tmp").exists()
