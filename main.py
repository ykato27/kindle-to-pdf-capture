#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point for Kindle to PDF converter
"""

import sys

from kindle_to_pdf.cli import main

if __name__ == "__main__":
    sys.exit(main())
