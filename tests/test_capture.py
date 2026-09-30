from PIL import Image, ImageChops, ImageDraw

from kindle_capture import capture

from conftest import FakeScreen, make_config, make_page


def saved_names(config):
    return sorted(p.name for p in config.images_dir.iterdir())


def test_stops_after_three_identical_screens_and_drops_the_repeats(tmp_path, stop):
    config = make_config(tmp_path)
    screen = FakeScreen([make_page(i) for i in range(5)])

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "end_of_book"
    assert [p.name for p in result.pages] == [f"page_{i:04d}.png" for i in range(1, 6)]
    assert saved_names(config) == [p.name for p in result.pages]


def test_stops_when_the_screen_flickers_between_two_states(tmp_path, stop):
    # 表紙から進まず、クリックのたびにツールバーが出たり消えたりする状態
    cover = make_page(0)
    with_toolbar = cover.copy()
    ImageDraw.Draw(with_toolbar).rectangle((0, 0, 864, 40), fill="gray")

    class Flicker(FakeScreen):
        def screenshot(self):
            return (cover if self.turns % 2 == 0 else with_toolbar).copy()

    config = make_config(tmp_path)
    screen = Flicker([cover])

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "end_of_book"
    assert len(result.pages) == 2
    assert screen.turns == 3


def saved_sources(result, pages):
    """Index of the source page each saved image shows."""

    found = []
    for path in result.pages:
        saved = Image.open(path).convert("RGB")
        found.append(next(i for i, page in enumerate(pages) if ImageChops.difference(saved, page).getbbox() is None))
    return found


def test_slow_page_render_does_not_lose_pages(tmp_path, stop):
    # ページ送りの後、3回撮るまで前のページが写ったままになる描画の遅れ
    pages = [make_page(i) for i in range(4)]
    config = make_config(tmp_path)
    screen = FakeScreen(pages, lag=3)

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "end_of_book"
    assert saved_sources(result, pages) == [0, 1, 2, 3]


def test_page_that_repeats_an_earlier_one_is_kept_when_the_book_goes_on(tmp_path, stop):
    blank = make_page(99)
    pages = [make_page(1), blank, make_page(2), blank.copy(), make_page(3)]
    config = make_config(tmp_path)
    screen = FakeScreen(pages)

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "end_of_book"
    assert len(result.pages) == 5


def test_stop_event_keeps_the_pages_taken_so_far(tmp_path, stop):
    config = make_config(tmp_path)
    screen = FakeScreen([make_page(i) for i in range(10)])

    def turn_and_stop_after_two():
        screen.turn_page()
        if screen.turns == 2:
            stop.set()

    result = capture.capture_book(config, screen.screenshot, turn_and_stop_after_two, stop)

    assert result.reason == "stopped"
    assert len(result.pages) == 2
    assert saved_names(config) == ["page_0001.png", "page_0002.png"]


def test_stopping_right_after_a_stall_drops_the_provisional_duplicate(tmp_path, stop):
    config = make_config(tmp_path)
    screen = FakeScreen([make_page(1), make_page(2)])

    def turn_and_stop_after_stall():
        screen.turn_page()
        if screen.turns == 3:  # 3枚目（2枚目の重複）を仮保存した後
            stop.set()

    result = capture.capture_book(config, screen.screenshot, turn_and_stop_after_stall, stop)

    assert result.reason == "stopped"
    assert saved_names(config) == ["page_0001.png", "page_0002.png"]


def test_max_pages_limits_the_capture(tmp_path, stop):
    config = make_config(tmp_path, max_pages=3)
    screen = FakeScreen([make_page(i) for i in range(10)])

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "max_pages"
    assert len(result.pages) == 3
    assert screen.turns == 2


def test_switching_away_from_kindle_stops_without_sending_keys(tmp_path, stop):
    config = make_config(tmp_path)
    screen = FakeScreen([make_page(i) for i in range(10)])
    # 2ページ撮った後、ページを送る前に別のアプリが前面に出る
    checks = iter([True, True, True, False])

    result = capture.capture_book(
        config, screen.screenshot, screen.turn_page, stop, lambda: next(checks)
    )

    assert result.reason == "focus_lost"
    assert len(result.pages) == 2
    assert screen.turns == 1


def test_fail_safe_exception_stops_and_keeps_pages(tmp_path, stop):
    class FailSafe(Exception):
        pass

    config = make_config(tmp_path)
    screen = FakeScreen([make_page(i) for i in range(10)])

    def turn_until_corner():
        if screen.turns == 2:
            raise FailSafe
        screen.turn_page()

    result = capture.capture_book(
        config, screen.screenshot, turn_until_corner, stop, stop_exceptions=(FailSafe,)
    )

    assert result.reason == "stopped"
    assert len(result.pages) == 3


def test_unexpected_error_keeps_pages_and_leaves_no_partial_file(tmp_path, stop):
    config = make_config(tmp_path)
    screen = FakeScreen([make_page(i) for i in range(10)])
    shots = 0

    def screenshot():
        nonlocal shots
        shots += 1
        if shots == 3:
            raise OSError("disk full")
        return screen.screenshot()

    result = capture.capture_book(config, screenshot, screen.turn_page, stop)

    assert result.reason == "error"
    assert len(result.pages) == 2
    assert saved_names(config) == ["page_0001.png", "page_0002.png"]


def test_prepare_folder_removes_previous_pages_and_partial_files(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    for name in ("page_0001.png", "page_0002.tmp", "note.txt"):
        (images / name).write_bytes(b"x")

    capture.prepare_folder(images)

    assert sorted(p.name for p in images.iterdir()) == ["note.txt"]


def test_blank_tiny_title_blank_does_not_end_the_book(tmp_path, stop):
    # 白紙 → 1文字だけの扉（白紙との差が約0.01%）→ 白紙 の並びで途中停止しないこと
    blank = make_page(1)
    ImageDraw.Draw(blank).rectangle((216, 0, 648, 558), fill="white")
    title = blank.copy()
    ImageDraw.Draw(title).rectangle((430, 270, 438, 276), fill="black")
    pages = [make_page(2), blank, title, blank.copy(), make_page(3)]
    config = make_config(tmp_path)
    screen = FakeScreen(pages)

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "end_of_book"
    assert len(result.pages) == 5


def test_max_pages_is_not_exceeded_by_a_provisional_frame(tmp_path, stop):
    blank = make_page(99)
    pages = [make_page(1), blank, blank.copy(), make_page(2), make_page(3)]
    config = make_config(tmp_path, max_pages=3)

    class Stuck(FakeScreen):
        # 白紙で1回だけページ送りが効かない
        def turn_page(self):
            self.turns += 1
            if self.turns != 2:
                self.index = min(self.index + 1, len(self.pages) - 1)

    screen = Stuck([pages[0], pages[1], pages[3], pages[4]])

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "max_pages"
    assert len(result.pages) == 3
    assert saved_names(config) == ["page_0001.png", "page_0002.png", "page_0003.png"]


def test_failed_save_leaves_neither_the_page_nor_a_partial_file(tmp_path, stop, monkeypatch):
    config = make_config(tmp_path)
    screen = FakeScreen([make_page(i) for i in range(10)])
    real_save = capture._save

    def save(image, path):
        if path.name == "page_0003.png":
            image.save(path.with_suffix(".tmp"), "PNG")
            raise OSError("disk full")
        real_save(image, path)

    monkeypatch.setattr(capture, "_save", save)

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "error"
    assert [p.name for p in result.pages] == ["page_0001.png", "page_0002.png"]
    assert "page_0003.png" not in saved_names(config)


def stuck_after_two_pages():
    return FakeScreen([make_page(1), make_page(2)])


def test_focus_lost_after_a_stall_drops_the_duplicate(tmp_path, stop):
    config = make_config(tmp_path)
    screen = stuck_after_two_pages()

    def ready():
        return screen.turns < 3  # 重複を仮保存した直後、ページを送る前に前面が変わる

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop, ready)

    assert result.reason == "focus_lost"
    assert saved_names(config) == ["page_0001.png", "page_0002.png"]


def test_error_after_a_stall_drops_the_duplicate(tmp_path, stop):
    config = make_config(tmp_path)
    screen = stuck_after_two_pages()

    def turn_page():
        if screen.turns == 2:  # 重複を仮保存した後のページ送りで失敗する
            raise RuntimeError("boom")
        screen.turn_page()

    result = capture.capture_book(config, screen.screenshot, turn_page, stop)

    assert result.reason == "error"
    assert saved_names(config) == ["page_0001.png", "page_0002.png"]
