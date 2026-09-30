"""Command line entrypoint for Kindle capture."""

from __future__ import annotations

import threading

from . import capture, config, kindle_app, pdf
from .stopkey import EscToStop

_REASONS = {
    "end_of_book": "ページが進まなくなったので、本の終わりとみなして止めました。",
    "max_pages": "指定した最大ページ数に達しました。",
    "stopped": "撮影を止めました。",
    "focus_lost": "Kindle が前面でなくなったので止めました（ほかのアプリにキーを送らないため）。",
    "error": "エラーで撮影を止めました。",
}


def _check_permissions() -> bool:
    required, optional = kindle_app.missing_permissions()
    if required:
        print(
            f"このターミナルに「{'」「'.join(required)}」の許可がありません。"
            "システム設定 > プライバシーとセキュリティ で許可し、ターミナルを開き直してから実行してください。"
        )
        return False
    if optional:
        print(
            "「入力監視」の許可がないため、Esc キーでは止められません。"
            "止めるときは別のアプリに切り替えるか、マウスを画面の角へ動かしてください。"
        )
    return True


def main() -> int:
    if not _check_permissions():
        return 1
    try:
        book_name = config.prompt_book_name()
        settings = config.CaptureConfig(book_name, output_root=config.OUTPUT_ROOT)
        existing = capture.list_pages(settings.images_dir)
        action = config.prompt_existing_images(len(existing)) if existing else "capture"
        if action == "cancel":
            return 1
        capture_settings = config.prompt_capture_settings() if action == "capture" else {}
        settings = config.CaptureConfig(
            book_name,
            quality=config.prompt_quality(),
            output_root=config.OUTPUT_ROOT,
            **capture_settings,
        )
    except (KeyboardInterrupt, EOFError):
        print("\n中止しました。")
        return 1

    if action == "pdf":
        pages = existing
    else:
        capture.prepare_folder(settings.images_dir)
        stop = threading.Event()
        with EscToStop(stop):
            result = capture.run(settings, stop)
        print(_REASONS[result.reason])
        pages = result.pages
        if result.reason == "end_of_book" and len(pages) <= 2:
            print(
                "最初のページからほとんど進みませんでした。ページを進める向き（R/L）"
                "と送り方（K/C）を確かめてください。"
            )

    if not pages:
        print("撮影したページがないため、PDF は作りませんでした。")
        return 1
    try:
        pdf.images_to_pdf(pages, settings.output_pdf, settings.quality)
    except KeyboardInterrupt:
        print(
            "\nPDF の作成を中断しました。撮影した画像は残っています。"
            "同じ書籍名で起動し「P=この画像からPDFだけ作る」を選ぶと作り直せます。"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
