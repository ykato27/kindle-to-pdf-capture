#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core converter module for capturing and converting Kindle books to PDF
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional

import imagehash
import pyautogui
import pygetwindow as gw
from PIL import Image

from .config import SystemConfig, get_default_config
from .logger import get_logger
from .utils import get_pdf_filename

logger = get_logger(__name__)


class KindleToPdfConverter:
    """Kindleから本を自動キャプチャしてPDFに変換するクラス"""

    def __init__(self, config: Optional[SystemConfig] = None) -> None:
        """
        初期化

        Args:
            config: システム設定。Noneの場合はデフォルト設定を使用
        """
        self.config = config or get_default_config()
        self.temp_dir = tempfile.mkdtemp(prefix="kindle_capture_")
        self.screenshots: List[Image.Image] = []
        self.previous_hash: Optional[str] = None
        self.same_page_count = 0

        logger.debug(f"Converter initialized with config: {self.config}")
        logger.debug(f"Temporary directory: {self.temp_dir}")

    def find_kindle_window(self) -> Optional[gw.Win32Window]:
        """
        Kindleアプリのウィンドウを検索して返す

        Returns:
            Kindleアプリのウィンドウオブジェクト、見つからない場合はNone
        """
        logger.info("Kindleアプリのウィンドウを検索中...")

        for window in gw.getAllWindows():
            if self.config.window.kindle_window_keyword in window.title.lower():
                logger.info(f"Kindleウィンドウが見つかりました: {window.title}")
                return window

        logger.error("Kindleアプリが見つかりません")
        return None

    def activate_window(self, window: gw.Win32Window) -> bool:
        """
        ウィンドウを前面に表示して有効化

        Args:
            window: 対象ウィンドウ

        Returns:
            成功時True
        """
        try:
            logger.info("Kindleウィンドウを前面に表示中...")
            window.activate()
            time.sleep(self.config.capture.window_activation_wait_time)
            logger.debug("ウィンドウの有効化完了")
            return True
        except Exception as e:
            logger.error(f"ウィンドウの有効化に失敗: {e}")
            return False

    def capture_screenshot(self) -> Image.Image:
        """
        スクリーンショットを取得

        Returns:
            キャプチャした画像オブジェクト
        """
        return pyautogui.screenshot()

    def calculate_image_hash(self, image: Image.Image) -> str:
        """
        画像のハッシュ値を計算

        Args:
            image: 対象画像

        Returns:
            画像のハッシュ値（文字列）
        """
        return str(imagehash.average_hash(image))

    def are_images_same(self, hash1: Optional[str], hash2: str) -> bool:
        """
        2つの画像が同じかどうかを判定

        Args:
            hash1: 最初のハッシュ値
            hash2: 次のハッシュ値

        Returns:
            同じと判定された場合True
        """
        if hash1 is None:
            return False

        # ハッシュ値が完全一致するかチェック
        is_same = hash1 == hash2
        if is_same:
            logger.debug("画像ハッシュが一致しました")
        return is_same

    def turn_page(self) -> None:
        """右矢印キーでページめくり"""
        logger.debug("ページをめくります")
        pyautogui.press("right")

    def capture_and_save(self, page_num: int) -> Image.Image:
        """
        スクリーンショットを取得して一時フォルダに保存

        Args:
            page_num: ページ番号

        Returns:
            キャプチャした画像オブジェクト
        """
        screenshot = self.capture_screenshot()
        temp_path = Path(self.temp_dir) / f"page_{page_num:04d}.png"
        screenshot.save(temp_path)
        logger.info(f"ページ {page_num} をキャプチャしました")
        return screenshot

    def process_book(self, book_title: str) -> bool:
        """
        本のスクリーンショットを取得してPDFに変換

        Args:
            book_title: 本のタイトル（ファイル名として使用）

        Returns:
            成功時True
        """
        try:
            # Kindleウィンドウを検索
            kindle_window = self.find_kindle_window()
            if not kindle_window:
                logger.error("Kindleアプリが見つかりません")
                logger.info("Kindleアプリを起動して、読みたい本を開いてください")
                return False

            # ウィンドウを前面に表示
            if not self.activate_window(kindle_window):
                return False

            logger.info("本のキャプチャを開始します")
            logger.info("スクリーンショット取得中は、ウィンドウを動かさないでください")

            # 初回スクリーンショット取得
            logger.info("初回スクリーンショットを取得中...")
            image = self.capture_and_save(1)
            self.previous_hash = self.calculate_image_hash(image)
            self.screenshots.append(image)
            self.same_page_count = 0

            page_num = 2

            # ページめくりループ
            while page_num <= self.config.capture.max_pages:
                # ページめくり
                self.turn_page()
                time.sleep(self.config.capture.page_turn_wait_time)

                # スクリーンショット取得
                image = self.capture_and_save(page_num)
                current_hash = self.calculate_image_hash(image)

                # 画像比較
                if self.are_images_same(self.previous_hash, current_hash):
                    self.same_page_count += 1
                    logger.info(
                        f"同じページが検出されました "
                        f"({self.same_page_count}/{self.config.capture.max_same_page_count})"
                    )

                    if self.same_page_count >= self.config.capture.max_same_page_count:
                        logger.info("最終ページに到達しました。キャプチャ処理を終了します")
                        break
                else:
                    self.same_page_count = 0
                    self.screenshots.append(image)

                self.previous_hash = current_hash
                page_num += 1

            logger.info(f"合計 {len(self.screenshots)} ページをキャプチャしました")

            # PDFに変換
            return self.create_pdf(book_title)

        except KeyboardInterrupt:
            logger.warning("処理が中断されました")
            return False
        except Exception as e:
            logger.exception(f"エラーが発生しました: {e}")
            return False
        finally:
            self.cleanup()

    def create_pdf(self, book_title: str) -> bool:
        """
        キャプチャした画像をPDFに変換して保存

        Args:
            book_title: 本のタイトル（ファイル名として使用）

        Returns:
            成功時True
        """
        try:
            if not self.screenshots:
                logger.error("キャプチャした画像がありません")
                return False

            logger.info("PDFを作成中...")

            # PDFパスを生成
            pdf_path = get_pdf_filename(book_title, self.config.output_dir)

            # 画像をRGBに変換してPDFに変換
            pdf_images = []
            for img in self.screenshots:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                pdf_images.append(img)

            # PDFを保存
            if pdf_images:
                pdf_images[0].save(
                    pdf_path,
                    save_all=True,
                    append_images=pdf_images[1:],
                    quality=self.config.pdf.quality,
                )
                logger.info(f"PDF作成完了: {pdf_path}")
                return True

            return False

        except Exception as e:
            logger.exception(f"PDF作成エラー: {e}")
            return False

    def cleanup(self) -> None:
        """一時フォルダをクリーンアップ"""
        if not self.config.pdf.cleanup_temp_files:
            logger.debug(f"一時ファイルをスキップしました: {self.temp_dir}")
            return

        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("一時ファイルをクリーンアップしました")
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")
