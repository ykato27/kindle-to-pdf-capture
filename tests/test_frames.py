import random

from PIL import Image, ImageChops, ImageDraw

from kindle_capture import frames

from conftest import make_page


def test_same_screen_is_same_page():
    a = frames.fingerprint(make_page(1))
    b = frames.fingerprint(make_page(1))
    assert frames.is_same_page(a, b)


def test_slight_brightness_noise_is_still_the_same_page():
    page = make_page(1)
    rng = random.Random(0)
    noise = Image.new("L", page.size)
    noise.putdata([rng.randint(0, 20) for _ in range(page.width * page.height)])
    noisy = ImageChops.add(page, Image.merge("RGB", [noise] * 3))
    assert frames.is_same_page(frames.fingerprint(page), frames.fingerprint(noisy))


def test_different_text_pages_are_different():
    a = frames.fingerprint(make_page(1))
    b = frames.fingerprint(make_page(2))
    assert frames.changed_ratio(a, b) > 0.05
    assert not frames.is_same_page(a, b)


def test_small_title_on_blank_page_counts_as_a_new_page():
    blank = make_page(1)
    ImageDraw.Draw(blank).rectangle((216, 0, 648, 558), fill="white")
    title = blank.copy()
    # 画面の約0.1%を占める小さな見出し（章の扉ページ相当）
    ImageDraw.Draw(title).rectangle((400, 250, 440, 258), fill="black")
    assert not frames.is_same_page(frames.fingerprint(blank), frames.fingerprint(title))


def test_mismatched_sizes_are_different():
    a = frames.fingerprint(make_page(1, size=(864, 558)))
    b = frames.fingerprint(make_page(1, size=(864, 600)))
    assert frames.changed_ratio(a, b) == 1.0
