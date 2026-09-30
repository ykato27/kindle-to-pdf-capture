"""Settings for one capture session, collected interactively."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, TypeVar

OUTPUT_ROOT = Path.home() / "kindle_capture"

# 次のページへ進む向き。横書きの本は右、縦書き（右開き）の本は左
DIRECTIONS = {"R": "right", "L": "left"}
# ページ送りの方法。クリックはキーが効かない環境向けの予備
NAVIGATIONS = {"K": "key", "C": "click"}
MAX_SECONDS = 60


@dataclass(frozen=True)
class PdfQuality:
    """PDF に入れる画像の縮小と圧縮の度合い."""

    max_height: int | None  # ページ画像の高さの上限（px）。None は縮小しない
    jpeg_quality: int


QUALITIES = {
    "S": PdfQuality(max_height=1200, jpeg_quality=60),  # 標準: 元の約1/3の容量
    "L": PdfQuality(max_height=900, jpeg_quality=50),  # 軽量
    "H": PdfQuality(max_height=None, jpeg_quality=75),  # 高画質: 撮影した解像度のまま
}


@dataclass(frozen=True)
class CaptureConfig:
    book_name: str
    max_pages: int = 1000
    direction: str = "right"
    navigation: str = "key"
    capture_interval: float = 0.5
    page_change_interval: float = 1.0
    quality: PdfQuality = field(default_factory=lambda: QUALITIES["S"])
    output_root: Path = OUTPUT_ROOT

    @property
    def book_dir(self) -> Path:
        return self.output_root / sanitize_book_name(self.book_name)

    @property
    def images_dir(self) -> Path:
        return self.book_dir / "images"

    @property
    def output_pdf(self) -> Path:
        return self.book_dir / f"{sanitize_book_name(self.book_name)}.pdf"


def sanitize_book_name(book_name: str) -> str:
    """A single folder name: no path separators, no leading/trailing dots."""

    sanitized = "_".join(book_name.replace("/", " ").replace("\\", " ").split()).strip(".")
    return sanitized or "book"


T = TypeVar("T")


def _ask(text: str, default: str, parse: Callable[[str], T]) -> T:
    """Prompt until `parse` accepts the answer (it raises ValueError to reject)."""

    while True:
        answer = input(f"{text} [{default}]: ").strip() or default
        try:
            return parse(answer)
        except ValueError as exc:
            print(f"  入力を確認してください: {exc}")


def _choice(options: dict[str, T]) -> Callable[[str], T]:
    def parse(answer: str) -> T:
        key = answer.upper()
        if key not in options:
            raise ValueError(f"{' / '.join(options)} のいずれかを入力してください")
        return options[key]

    return parse


def _positive_int(answer: str) -> int:
    try:
        value = int(answer)
    except ValueError:
        raise ValueError("整数を入力してください") from None
    if value <= 0:
        raise ValueError("1以上の整数を入力してください")
    return value


def _seconds(answer: str) -> float:
    try:
        value = float(answer)
    except ValueError:
        raise ValueError("秒数を数字で入力してください") from None
    if not math.isfinite(value) or not 0 <= value <= MAX_SECONDS:
        raise ValueError(f"0〜{MAX_SECONDS} の秒数を入力してください")
    return value


def prompt_book_name() -> str:
    return _ask("書籍名（保存フォルダとPDFの名前になります）", "MyBook", str)


def prompt_existing_images(count: int) -> str:
    """What to do with images left from a previous run: "pdf", "capture" or "cancel"."""

    return _ask(
        f"前回撮影した画像が {count} 枚あります。"
        "P=この画像からPDFだけ作る / N=消して撮り直す / Q=中止",
        "P",
        _choice({"P": "pdf", "N": "capture", "Q": "cancel"}),
    )


def prompt_capture_settings() -> dict:
    return dict(
        max_pages=_ask(
            "最大ページ数（本の終わりは自動で検出して止まります）", "1000", _positive_int
        ),
        direction=_ask(
            "ページを進める向き R=右（横書きの本） / L=左（縦書きの本）",
            "R",
            _choice(DIRECTIONS),
        ),
        navigation=_ask(
            "ページ送りの方法 K=矢印キー / C=画面の端をクリック",
            "K",
            _choice(NAVIGATIONS),
        ),
        capture_interval=_ask("撮影してからページを送るまでの秒数", "0.5", _seconds),
        page_change_interval=_ask("ページを送ってから撮影するまでの秒数", "1.0", _seconds),
    )


def prompt_quality() -> PdfQuality:
    return _ask(
        "PDFの画質 S=標準 / L=軽量 / H=高画質（容量は約3倍）",
        "S",
        _choice(QUALITIES),
    )
