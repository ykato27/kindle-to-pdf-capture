import pytest

from kindle_capture import capture, cli, kindle_app, pdf

from conftest import make_page


def feed(monkeypatch, *answers):
    it = iter(answers)
    asked = []

    def answer(prompt):
        asked.append(prompt)
        return next(it)

    monkeypatch.setattr("builtins.input", answer)
    return asked


def setup(monkeypatch, tmp_path, missing=([], [])):
    monkeypatch.setattr("kindle_capture.config.OUTPUT_ROOT", tmp_path)
    monkeypatch.setattr(kindle_app, "missing_permissions", lambda: missing)
    made = []
    monkeypatch.setattr(pdf, "images_to_pdf", lambda pages, out, quality: made.append((pages, out, quality)))
    return made


def no_capture(monkeypatch):
    monkeypatch.setattr(capture, "run", lambda *a: (_ for _ in ()).throw(AssertionError("captured")))


def previous_images(tmp_path, count=2):
    images = tmp_path / "本" / "images"
    images.mkdir(parents=True)
    for i in range(1, count + 1):
        make_page(i).save(images / f"page_{i:04d}.png")
    return images


def test_missing_permission_stops_before_the_capture_settings(monkeypatch, tmp_path, capsys):
    setup(monkeypatch, tmp_path, missing=(["アクセシビリティ"], []))
    asked = feed(monkeypatch, "本")
    no_capture(monkeypatch)

    assert cli.main() == 1
    assert len(asked) == 1  # 書籍名だけ聞いて止まる
    assert "アクセシビリティ" in capsys.readouterr().out


def test_pdf_only_works_without_screen_permissions(monkeypatch, tmp_path):
    made = setup(monkeypatch, tmp_path, missing=(["画面収録", "アクセシビリティ"], []))
    previous_images(tmp_path)
    feed(monkeypatch, "本", "P", "S")
    no_capture(monkeypatch)

    assert cli.main() == 0
    assert len(made[0][0]) == 2


def test_capture_then_pdf_from_the_captured_pages(monkeypatch, tmp_path):
    made = setup(monkeypatch, tmp_path)
    feed(monkeypatch, "本", "", "", "", "", "", "")

    def fake_run(settings, stop):
        page = settings.images_dir / "page_0001.png"
        make_page(1).save(page)
        return capture.CaptureResult([page], "end_of_book")

    monkeypatch.setattr(capture, "run", fake_run)

    assert cli.main() == 0
    assert len(made) == 1 and made[0][0][0].name == "page_0001.png"


def test_enter_on_existing_images_makes_a_pdf_and_keeps_them(monkeypatch, tmp_path):
    made = setup(monkeypatch, tmp_path)
    images = previous_images(tmp_path)
    feed(monkeypatch, "本", "", "L")  # 既定値は P（PDF だけ作る）
    no_capture(monkeypatch)

    assert cli.main() == 0
    pages, _, quality = made[0]
    assert [p.name for p in pages] == ["page_0001.png", "page_0002.png"]
    assert quality.max_height == 900
    assert sorted(p.name for p in images.iterdir()) == ["page_0001.png", "page_0002.png"]


def test_quit_on_existing_images_keeps_them(monkeypatch, tmp_path):
    made = setup(monkeypatch, tmp_path)
    images = previous_images(tmp_path)
    feed(monkeypatch, "本", "Q")
    no_capture(monkeypatch)

    assert cli.main() == 1
    assert made == []
    assert len(list(images.iterdir())) == 2


@pytest.mark.parametrize("error", [KeyboardInterrupt, EOFError])
def test_ctrl_c_or_closed_input_at_a_question_exits_cleanly(monkeypatch, tmp_path, capsys, error):
    setup(monkeypatch, tmp_path)

    def interrupt(_):
        raise error

    monkeypatch.setattr("builtins.input", interrupt)

    assert cli.main() == 1
    assert "中止しました" in capsys.readouterr().out


@pytest.mark.parametrize("error", [KeyboardInterrupt(), OSError("page_0002.png を読めません")])
def test_pdf_failure_keeps_the_images_and_explains_how_to_retry(monkeypatch, tmp_path, capsys, error):
    setup(monkeypatch, tmp_path)
    images = previous_images(tmp_path)
    feed(monkeypatch, "本", "P", "S")

    def fail(*_):
        raise error

    monkeypatch.setattr(pdf, "images_to_pdf", fail)

    assert cli.main() == 1
    assert "P=この画像からPDFだけ作る" in capsys.readouterr().out
    assert len(list(images.iterdir())) == 2
