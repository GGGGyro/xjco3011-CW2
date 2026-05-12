"""Project-local third-party dependency bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

VENDOR_PATH = Path(__file__).resolve().parent.parent / ".vendor"

if VENDOR_PATH.exists():
    vendor_str = str(VENDOR_PATH)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)
