#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for Kindle to PDF converter
"""

import sys
from pathlib import Path

from .config import get_config_from_env, get_default_config
from .converter import KindleToPdfConverter
from .logger import setup_logger
from .utils import create_output_directory, get_onedrive_desktop_path

logger = setup_logger("kindle_to_pdf")


def print_header() -> None:
    """ヘッダーを表示"""
    print("=" * 60)
    print("Kindle自動スクリーンショット＆PDF化システム")
    print("=" * 60)
    print()


def get_default_output_dir() -> Path:
    """
    デフォルト出力ディレクトリを取得
    OneDriveデスクトップを優先、なければカレントディレクトリ

    Returns:
        出力ディレクトリパス
    """
    onedrive_path = get_onedrive_desktop_path()
    if onedrive_path and onedrive_path.exists():
        return onedrive_path

    # フォールバック: カレントディレクトリ
    return Path.cwd()


def get_user_input() -> tuple[str, Path]:
    """
    ユーザー入力を取得

    Returns:
        (本のタイトル, 出力ディレクトリ)の タプル
    """
    default_output = get_default_output_dir()

    # 出力ディレクトリの指定
    print("出力先フォルダを指定してください。")
    print(f"（デフォルト: {default_output}）")
    output_dir_input = input("出力先フォルダ [デフォルト]: ").strip()

    if output_dir_input:
        output_dir = create_output_directory(Path(output_dir_input))
    else:
        output_dir = create_output_directory(default_output)
        logger.info(f"デフォルト出力ディレクトリを使用: {output_dir}")

    # 本のタイトル入力
    print()
    book_title = input("本のタイトルを入力してください: ").strip()
    if not book_title:
        logger.error("タイトルが入力されていません")
        sys.exit(1)

    return book_title, output_dir


def main() -> int:
    """
    メイン処理

    Returns:
        終了コード（0: 成功、1: 失敗）
    """
    try:
        print_header()

        # 設定を取得
        config = get_config_from_env()

        # ユーザー入力を取得
        book_title, output_dir = get_user_input()
        config.output_dir = output_dir

        print()
        logger.info("準備完了。処理を開始します...")
        print()

        # コンバーター作成
        converter = KindleToPdfConverter(config=config)

        # 処理実行
        success = converter.process_book(book_title)

        if success:
            print()
            print("=" * 60)
            print("処理が正常に完了しました！")
            print("=" * 60)
            return 0
        else:
            print()
            print("=" * 60)
            print("処理が失敗しました")
            print("=" * 60)
            return 1

    except KeyboardInterrupt:
        print("\n処理が中断されました")
        return 130
    except Exception as e:
        logger.exception(f"予期しないエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
