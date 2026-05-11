"""Tests for index persistence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.storage import load_index, save_index


class StorageTests(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        payload = {
            "index": {"alpha": {"https://example.com": {"freq": 1, "positions": [0]}}},
            "pages": {"https://example.com": "Example"},
            "page_word_counts": {"https://example.com": 1},
            "document_count": 1,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "index.json"
            save_index(payload, path)
            restored = load_index(path)

        self.assertEqual(payload, restored)


if __name__ == "__main__":
    unittest.main()
