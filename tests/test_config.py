import pytest

from kindle_capture import config


@pytest.mark.parametrize(
    "name, expected",
    [("My Book", "My_Book"), ("..", "book"), ("../etc", "_etc"), ("a/b\\c", "a_b_c"), ("  ", "book")],
)
def test_book_name_stays_a_single_folder(name, expected):
    assert config.sanitize_book_name(name) == expected


@pytest.mark.parametrize("answer", ["abc", "-1", "inf", "nan", "61", "1e10"])
def test_seconds_reject_unusable_values(answer):
    with pytest.raises(ValueError):
        config._seconds(answer)


def test_seconds_accept_normal_values():
    assert config._seconds("0") == 0
    assert config._seconds("1.5") == 1.5


@pytest.mark.parametrize("answer", ["0", "-3", "1.5", "abc", "10000"])
def test_page_count_rejects_non_positive_integers(answer):
    with pytest.raises(ValueError):
        config._positive_int(answer)


def test_prompt_repeats_until_the_answer_is_valid(monkeypatch, capsys):
    answers = iter(["x", "L"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert config.prompt_quality() == config.QUALITIES["L"]
    assert "のいずれかを入力してください" in capsys.readouterr().out


def test_long_book_name_fits_in_a_file_name():
    name = config.sanitize_book_name("長" * 300)
    assert len(name.encode("utf-8")) <= config.MAX_NAME_BYTES
    assert name == "長" * (config.MAX_NAME_BYTES // 3)
