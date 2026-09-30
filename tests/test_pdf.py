from PIL import PdfParser

from kindle_capture import pdf
from kindle_capture.config import QUALITIES, PdfQuality

from conftest import make_page


def page_sizes(path):
    parser = PdfParser.PdfParser(str(path))
    try:
        return [tuple(parser.read_indirect(ref)[b"MediaBox"][2:]) for ref in parser.pages]
    finally:
        parser.close()


def make_images(tmp_path, count, size=(1728, 1116)):
    paths = []
    for i in range(count):
        path = tmp_path / f"page_{i + 1:04d}.png"
        make_page(i, size=size).save(path)
        paths.append(path)
    return paths


def test_pdf_has_every_page_scaled_to_the_height_limit(tmp_path):
    paths = make_images(tmp_path, 3)

    output = pdf.images_to_pdf(paths, tmp_path / "book.pdf", PdfQuality(max_height=500, jpeg_quality=60))

    assert page_sizes(output) == [(774, 500)] * 3
    assert not (tmp_path / "book.pdf.tmp").exists()


def test_high_quality_keeps_the_captured_size(tmp_path):
    paths = make_images(tmp_path, 1, size=(900, 600))

    output = pdf.images_to_pdf(paths, tmp_path / "book.pdf", QUALITIES["H"])

    assert page_sizes(output) == [(900, 600)]


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
    assert len(page_sizes(tmp_path / "160.pdf")) == 160
