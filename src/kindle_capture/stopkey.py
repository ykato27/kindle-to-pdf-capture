"""Stop the capture with the Esc key while Kindle is in front."""

from __future__ import annotations

import threading


class EscToStop:
    """Set `event` when Esc is pressed anywhere, until the block exits.

    On macOS the terminal app needs the Input Monitoring permission
    (システム設定 > プライバシーとセキュリティ > 入力監視); without it no key is
    seen. cli checks that permission before the capture starts.
    """

    def __init__(self, event: threading.Event) -> None:
        self.event = event
        self._listener = None

    def __enter__(self) -> "EscToStop":
        try:
            from pynput import keyboard

            def on_press(key) -> None:
                if key == keyboard.Key.esc:
                    self.event.set()

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.start()
            self._listener.wait()
        except Exception as exc:  # noqa: BLE001  環境によっては監視を始められない
            self._listener = None
            print(f"Esc キーでの停止は使えません（{exc}）。別のアプリに切り替えるか、マウスを画面の角へ動かすと止まります。")
        return self

    def __exit__(self, *exc_info) -> None:
        if self._listener is not None:
            self._listener.stop()
