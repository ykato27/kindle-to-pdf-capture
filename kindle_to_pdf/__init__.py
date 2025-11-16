#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle to PDF Capture - Automatically capture pages from Kindle and convert them to PDF
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

from .config import SystemConfig, get_config_from_env, get_default_config
from .converter import KindleToPdfConverter

__all__ = [
    "KindleToPdfConverter",
    "SystemConfig",
    "get_default_config",
    "get_config_from_env",
]
