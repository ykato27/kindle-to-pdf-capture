from PIL import ImageDraw

from kindle_capture import capture

from conftest import FakeScreen, make_config, make_page


def saved_names(config):
    return sorted(p.name for p in config.images_dir.glob("page_*.png"))


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


def test_slow_page_render_does_not_lose_pages(tmp_path, stop):
    pages = [make_page(i) for i in range(4)]
    config = make_config(tmp_path)
    screen = FakeScreen(pages, lag=1)

    result = capture.capture_book(config, screen.screenshot, screen.turn_page, stop)

    assert result.reason == "end_of_book"
    assert len(result.pages) == 4


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
