from PIL import Image, PdfParser

from kindle_capture import pdf
from kindle_capture.config import PdfQuality

from conftest import make_page


def page_sizes(path):
    parser = PdfParser.PdfParser(str(path))
    try:
        return [tuple(parser.read_indirect(ref)[b"MediaBox"][2:]) for ref in parser.pages]
    finally:
        parser.close()


def test_pdf_has_every_page_cropped_and_scaled(tmp_path):
    paths = []
    for i in range(3):
        path = tmp_path / f"page_{i + 1:04d}.png"
        make_page(i, size=(1728, 1116)).save(path)
        paths.append(path)

    output = pdf.images_to_pdf(paths, tmp_path / "book.pdf", PdfQuality(max_height=500, jpeg_quality=60))

    sizes = page_sizes(output)
    assert len(sizes) == 3
    assert len(set(sizes)) == 1
    width, height = sizes[0]
    assert height == 500
    # 黒い余白を切り落とし、白いページ部分（元の幅の半分）に近い縦長になる
    assert width < height


def test_common_box_covers_every_page(tmp_path):
    narrow = Image.new("RGB", (800, 400), "black")
    narrow.paste("white", (300, 100, 500, 300))
    wide = Image.new("RGB", (800, 400), "black")
    wide.paste("white", (200, 150, 600, 250))
    paths = []
    for i, image in enumerate((narrow, wide)):
        path = tmp_path / f"page_{i}.png"
        image.save(path)
        paths.append(path)

    left, top, right, bottom = pdf.common_content_box(paths)

    assert left <= 200 and top <= 100 and right >= 600 and bottom >= 300
