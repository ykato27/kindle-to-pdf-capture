#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging configuration for Kindle to PDF converter
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    ロガーを設定して返す

    Args:
        name: ロガー名
        log_file: ログファイルパス。Noneの場合はコンソール出力のみ
        level: ログレベル

    Returns:
        設定済みのロガーオブジェクト
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # フォーマッターを定義
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラーを追加
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラーを追加（指定された場合）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """既存のロガーを取得"""
    return logging.getLogger(name)
