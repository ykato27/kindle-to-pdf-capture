"""Command line entrypoint for Kindle capture."""

from __future__ import annotations

import threading

from . import capture, config, pdf
from .stopkey import EscToStop

_REASONS = {
    "end_of_book": "同じ画面が3回続いたので、本の終わりとみなして止めました。",
    "max_pages": "指定した最大ページ数に達しました。",
    "stopped": "撮影を止めました。",
    "focus_lost": "Kindle が前面でなくなったので止めました（ほかのアプリにキーを送らないため）。",
}


def main() -> int:
    try:
        settings = config.prompt_config()
    except (KeyboardInterrupt, EOFError):
        print("\n中止しました。")
        return 1

    stop = threading.Event()
    with EscToStop(stop):
        result = capture.run(settings, stop)

    print(_REASONS[result.reason])
    if not result.pages:
        print("撮影したページがないため、PDF は作りませんでした。")
        return 1
    if result.reason == "end_of_book" and len(result.pages) == 1:
        print("1ページ目から進みませんでした。ページを進める向き（R/L）を逆にして試してください。")

    pdf.images_to_pdf(result.pages, settings.output_pdf, settings.quality)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
