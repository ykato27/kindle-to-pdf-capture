#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for Kindle to PDF converter
"""

from pathlib import Path
from typing import Optional


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    ファイル名として不正な文字を削除・置換する

    Args:
        filename: オリジナルのファイル名
        replacement: 置換文字列

    Returns:
        サニタイズされたファイル名
    """
    # 不正な文字を置換
    invalid_chars = '<>:"|?*\\'
    result = filename
    for char in invalid_chars:
        result = result.replace(char, replacement)

    # 先頭と末尾のスペースを削除
    result = result.strip()

    # 複数の連続スペースを1つにする
    while replacement + replacement in result:
        result = result.replace(replacement + replacement, replacement)

    return result if result else "document"


def create_output_directory(output_dir: Optional[Path]) -> Path:
    """
    出力ディレクトリを作成して返す

    Args:
        output_dir: 出力ディレクトリパス。Noneの場合はカレントディレクトリ

    Returns:
        出力ディレクトリパス
    """
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def validate_file_path(file_path: Path) -> bool:
    """
    ファイルパスの書き込み可能性を確認

    Args:
        file_path: 確認するファイルパス

    Returns:
        書き込み可能な場合True
    """
    parent_dir = file_path.parent
    if not parent_dir.exists():
        return False

    # 親ディレクトリの書き込み権限を確認
    return parent_dir.is_dir() and (parent_dir / "write_test").parent.exists()


def get_pdf_filename(book_title: str, output_dir: Path) -> Path:
    """
    PDFファイルのパスを生成

    Args:
        book_title: 本のタイトル
        output_dir: 出力ディレクトリ

    Returns:
        PDFファイルのパス
    """
    safe_title = sanitize_filename(book_title)
    pdf_path = output_dir / f"{safe_title}.pdf"
    return pdf_path
