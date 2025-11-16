#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle自動スクリーンショット＆PDF化システム
Windows版Kindleアプリから1ページずつ自動でスクリーンショットを取得し、
1冊の本を1つのPDFファイルにまとめるシステム
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List

import pyautogui
import pygetwindow as gw
from PIL import Image
import imagehash


class KindleToPdfConverter:
    """Kindleから本を自動キャプチャしてPDFに変換するクラス"""

    def __init__(self, output_dir: Optional[str] = None, similarity_threshold: float = 0.95):
        """
        初期化

        Args:
            output_dir: PDF出力ディレクトリ。Noneの場合はカレントディレクトリ
            similarity_threshold: 画像の類似度判定の閾値（0-1）。同一ページ判定に使用
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = similarity_threshold

        # 一時フォルダの作成
        self.temp_dir = tempfile.mkdtemp(prefix="kindle_capture_")
        self.screenshots: List[Image.Image] = []
        self.previous_hash = None
        self.same_page_count = 0
        self.max_same_page_count = 3  # 3回連続で同じページなら終了

    def find_kindle_window(self) -> Optional[gw.Win32Window]:
        """
        Kindleアプリのウィンドウを検索して返す

        Returns:
            Kindleアプリのウィンドウオブジェクト、見つからない場合はNone
        """
        print("Kindleアプリのウィンドウを検索中...")

        for window in gw.getAllWindows():
            if "kindle" in window.title.lower():
                print(f"見つかりました: {window.title}")
                return window

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
            print("Kindleウィンドウを前面に表示...")
            window.activate()
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"ウィンドウの有効化に失敗: {e}")
            return False

    def capture_screenshot(self) -> Image.Image:
        """
        スクリーンショットを取得

        Returns:
            キャプチャした画像オブジェクト
        """
        screenshot = pyautogui.screenshot()
        return screenshot

    def calculate_image_hash(self, image: Image.Image) -> str:
        """
        画像のハッシュ値を計算

        Args:
            image: 対象画像

        Returns:
            画像のハッシュ値（文字列）
        """
        return str(imagehash.average_hash(image))

    def are_images_same(self, hash1: str, hash2: str) -> bool:
        """
        2つの画像が同じかどうかを判定

        Args:
            hash1: 最初のハッシュ値
            hash2: 次のハッシュ値

        Returns:
            同じと判定された場合True
        """
        if hash1 is None or hash2 is None:
            return False

        # ハッシュ値が完全一致するかチェック
        return hash1 == hash2

    def turn_page(self) -> None:
        """右矢印キーでページめくり"""
        pyautogui.press('right')

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
        print(f"ページ {page_num} をキャプチャしました")
        return screenshot

    def process_book(self, book_title: str, max_pages: int = 10000) -> bool:
        """
        本のスクリーンショットを取得してPDFに変換

        Args:
            book_title: 本のタイトル（ファイル名として使用）
            max_pages: 最大ページ数（無限ループ防止）

        Returns:
            成功時True
        """
        try:
            # Kindleウィンドウを検索
            kindle_window = self.find_kindle_window()
            if not kindle_window:
                print("エラー: Kindleアプリが見つかりません。")
                print("Kindleアプリを起動して、読みたい本を開いてください。")
                return False

            # ウィンドウを前面に表示
            if not self.activate_window(kindle_window):
                return False

            print("\n本のキャプチャを開始します...")
            print("スクリーンショット取得中は、ウィンドウを動かさないでください。")
            print("Ctrl+C を押すと処理を中断できます。\n")

            # 初回スクリーンショット取得
            print("初回スクリーンショットを取得中...")
            image = self.capture_and_save(1)
            self.previous_hash = self.calculate_image_hash(image)
            self.screenshots.append(image)
            self.same_page_count = 0

            page_num = 2

            # ページめくりループ
            while page_num <= max_pages:
                # ページめくり
                self.turn_page()
                time.sleep(1.0)  # ページめくり後の待機

                # スクリーンショット取得
                image = self.capture_and_save(page_num)
                current_hash = self.calculate_image_hash(image)

                # 画像比較
                if self.are_images_same(self.previous_hash, current_hash):
                    self.same_page_count += 1
                    print(f"  → 同じページが検出されました ({self.same_page_count}/{self.max_same_page_count})")

                    if self.same_page_count >= self.max_same_page_count:
                        print(f"\n最終ページに到達しました。キャプチャ処理を終了します。")
                        break
                else:
                    self.same_page_count = 0  # カウントをリセット
                    self.screenshots.append(image)

                self.previous_hash = current_hash
                page_num += 1

            print(f"\n合計 {len(self.screenshots)} ページをキャプチャしました。")

            # PDFに変換
            return self.create_pdf(book_title)

        except KeyboardInterrupt:
            print("\n\n処理が中断されました。")
            return False
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
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
                print("エラー: キャプチャした画像がありません。")
                return False

            print("\nPDFを作成中...")

            # ファイル名を作成（不正な文字を削除）
            safe_title = "".join(c for c in book_title if c.isalnum() or c in ' -_')
            safe_title = safe_title.strip()
            if not safe_title:
                safe_title = "kindle_book"

            pdf_path = self.output_dir / f"{safe_title}.pdf"

            # 画像をRGBに変換してPDFに変換
            pdf_images = []
            for img in self.screenshots:
                # PDFのための変換
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                pdf_images.append(img)

            # PDFを保存
            if pdf_images:
                pdf_images[0].save(
                    pdf_path,
                    save_all=True,
                    append_images=pdf_images[1:],
                    quality=95
                )
                print(f"PDF作成完了: {pdf_path}")
                return True

            return False

        except Exception as e:
            print(f"PDF作成エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    def cleanup(self) -> None:
        """一時フォルダをクリーンアップ"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("一時ファイルをクリーンアップしました。")
        except Exception as e:
            print(f"クリーンアップ警告: {e}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("Kindle自動スクリーンショット＆PDF化システム")
    print("=" * 60)
    print()

    # 出力ディレクトリの指定
    print("出力先フォルダを指定してください。")
    print("（デフォルト: カレントディレクトリ）")
    output_dir = input("出力先フォルダ [デフォルト]: ").strip()
    if not output_dir:
        output_dir = None

    # 本のタイトル入力
    print()
    book_title = input("本のタイトルを入力してください: ").strip()
    if not book_title:
        print("タイトルが入力されていません。")
        return

    print()
    print("準備完了。処理を開始します...")
    print()

    # コンバーター作成
    converter = KindleToPdfConverter(output_dir=output_dir)

    # 処理実行
    success = converter.process_book(book_title)

    if success:
        print("\n" + "=" * 60)
        print("処理が正常に完了しました！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("処理が失敗しました。")
        print("=" * 60)


if __name__ == "__main__":
    main()
