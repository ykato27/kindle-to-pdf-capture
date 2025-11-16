#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for Kindle to PDF converter
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CaptureConfig:
    """スクリーンショットキャプチャ設定"""

    # ページめくり後の待機時間（秒）
    page_turn_wait_time: float = 1.0

    # ウィンドウ切り替え後の待機時間（秒）
    window_activation_wait_time: float = 0.5

    # 同一ページ判定の連続判定回数
    max_same_page_count: int = 3

    # 画像類似度の閾値（0-1）
    similarity_threshold: float = 0.95

    # 最大ページ数（無限ループ防止）
    max_pages: int = 10000


@dataclass
class PDFConfig:
    """PDF生成設定"""

    # PDF品質（0-95）
    quality: int = 95

    # 一時ファイル削除フラグ
    cleanup_temp_files: bool = True


@dataclass
class WindowConfig:
    """ウィンドウ検出設定"""

    # Kindleウィンドウタイトル検索キーワード
    kindle_window_keyword: str = "kindle"


@dataclass
class SystemConfig:
    """システム全体設定"""

    # キャプチャ設定
    capture: CaptureConfig

    # PDF生成設定
    pdf: PDFConfig

    # ウィンドウ検出設定
    window: WindowConfig

    # 出力ディレクトリ
    output_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.output_dir is None:
            self.output_dir = Path.cwd()
        else:
            self.output_dir = Path(self.output_dir)


def get_default_config() -> SystemConfig:
    """デフォルト設定を取得"""
    return SystemConfig(
        capture=CaptureConfig(),
        pdf=PDFConfig(),
        window=WindowConfig(),
    )


def get_config_from_env() -> SystemConfig:
    """環境変数から設定を読み込む"""
    import os

    config = get_default_config()

    # キャプチャ設定
    if os.getenv("KINDLE_PAGE_TURN_WAIT"):
        config.capture.page_turn_wait_time = float(
            os.getenv("KINDLE_PAGE_TURN_WAIT", "1.0")
        )

    if os.getenv("KINDLE_WINDOW_WAIT"):
        config.capture.window_activation_wait_time = float(
            os.getenv("KINDLE_WINDOW_WAIT", "0.5")
        )

    if os.getenv("KINDLE_MAX_SAME_PAGE"):
        config.capture.max_same_page_count = int(
            os.getenv("KINDLE_MAX_SAME_PAGE", "3")
        )

    if os.getenv("KINDLE_SIMILARITY_THRESHOLD"):
        config.capture.similarity_threshold = float(
            os.getenv("KINDLE_SIMILARITY_THRESHOLD", "0.95")
        )

    if os.getenv("KINDLE_MAX_PAGES"):
        config.capture.max_pages = int(os.getenv("KINDLE_MAX_PAGES", "10000"))

    # PDF設定
    if os.getenv("KINDLE_PDF_QUALITY"):
        config.pdf.quality = int(os.getenv("KINDLE_PDF_QUALITY", "95"))

    if os.getenv("KINDLE_CLEANUP_TEMP"):
        config.pdf.cleanup_temp_files = (
            os.getenv("KINDLE_CLEANUP_TEMP", "true").lower() == "true"
        )

    # ウィンドウ設定
    if os.getenv("KINDLE_WINDOW_KEYWORD"):
        config.window.kindle_window_keyword = os.getenv(
            "KINDLE_WINDOW_KEYWORD", "kindle"
        )

    # 出力ディレクトリ
    if os.getenv("KINDLE_OUTPUT_DIR"):
        config.output_dir = Path(os.getenv("KINDLE_OUTPUT_DIR", "."))

    return config
