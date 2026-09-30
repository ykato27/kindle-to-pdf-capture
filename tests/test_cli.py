from kindle_capture import capture, cli, kindle_app, pdf

from conftest import make_page


def feed(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(it))


def setup(monkeypatch, tmp_path, missing=([], [])):
    monkeypatch.setattr("kindle_capture.config.OUTPUT_ROOT", tmp_path)
    monkeypatch.setattr(kindle_app, "missing_permissions", lambda: missing)
    made = []
    monkeypatch.setattr(pdf, "images_to_pdf", lambda pages, out, quality: made.append((pages, out, quality)))
    return made


def test_missing_permission_stops_before_any_question(monkeypatch, tmp_path, capsys):
    setup(monkeypatch, tmp_path, missing=(["アクセシビリティ"], []))
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(AssertionError("asked")))

    assert cli.main() == 1
    assert "アクセシビリティ" in capsys.readouterr().out


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


def test_existing_images_can_be_turned_into_a_pdf_without_capturing(monkeypatch, tmp_path):
    made = setup(monkeypatch, tmp_path)
    images = tmp_path / "本" / "images"
    images.mkdir(parents=True)
    for i in (1, 2):
        make_page(i).save(images / f"page_{i:04d}.png")
    feed(monkeypatch, "本", "P", "L")
    monkeypatch.setattr(capture, "run", lambda *a: (_ for _ in ()).throw(AssertionError("captured")))

    assert cli.main() == 0
    pages, _, quality = made[0]
    assert [p.name for p in pages] == ["page_0001.png", "page_0002.png"]
    assert quality.max_height == 900


def test_ctrl_c_at_a_question_exits_cleanly(monkeypatch, tmp_path, capsys):
    setup(monkeypatch, tmp_path)

    def interrupt(_):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupt)

    assert cli.main() == 1
    assert "中止しました" in capsys.readouterr().out
