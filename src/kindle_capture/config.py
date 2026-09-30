"""Settings for one capture session, collected interactively."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

OUTPUT_ROOT = Path.home() / "kindle_capture"

# 次のページへ進む向き。横書きの本は右、縦書き（右開き）の本は左
DIRECTIONS = {"R": "right", "L": "left"}
# ページ送りの方法。クリックはキーが効かない環境向けの予備
NAVIGATIONS = {"K": "key", "C": "click"}


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
    max_pages: int
    direction: str
    navigation: str
    capture_interval: float
    page_change_interval: float
    quality: PdfQuality = QUALITIES["S"]
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
    sanitized = "_".join(book_name.replace("/", " ").split())
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
    value = int(answer)
    if value <= 0:
        raise ValueError("1以上の整数を入力してください")
    return value


def _non_negative_float(answer: str) -> float:
    value = float(answer)
    if value < 0:
        raise ValueError("0以上の数を入力してください")
    return value


def prompt_config() -> CaptureConfig:
    """Ask the user for every setting and return a validated config."""

    return CaptureConfig(
        book_name=_ask("書籍名（保存フォルダとPDFの名前になります）", "MyBook", str),
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
        capture_interval=_ask("撮影してからページを送るまでの秒数", "0.5", _non_negative_float),
        page_change_interval=_ask("ページを送ってから撮影するまでの秒数", "1.0", _non_negative_float),
        quality=_ask(
            "PDFの画質 S=標準 / L=軽量 / H=高画質（容量は約3倍）",
            "S",
            _choice(QUALITIES),
        ),
    )
