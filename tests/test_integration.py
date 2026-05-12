"""Integration-style tests across indexing, storage, and search."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.indexer import build_index
from src.models import PageContent
from src.search import find_pages, get_word_postings
from src.storage import load_index, save_index


class IntegrationTests(unittest.TestCase):
    def test_build_save_load_and_search_work_together(self) -> None:
        pages = [
            PageContent(
                "https://example.com/1",
                "Page One",
                "Good friends are honest friends",
            ),
            PageContent(
                "https://example.com/2",
                "Page Two",
                "Good ideas need patient work",
            ),
        ]

        index_data = build_index(pages)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "index.json"
            save_index(index_data, path)
            restored = load_index(path)

        postings = get_word_postings(restored, "friends")
        results = find_pages(restored, '"good friends"')

        self.assertIn("https://example.com/1", postings)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "https://example.com/1")

    def test_keyword_search_after_round_trip_keeps_ranking(self) -> None:
        pages = [
            PageContent("https://example.com/1", "One", "good good friends"),
            PageContent("https://example.com/2", "Two", "good friends patient careful work"),
        ]

        index_data = build_index(pages)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "index.json"
            save_index(index_data, path)
            restored = load_index(path)

        results = find_pages(restored, "good friends")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["url"], "https://example.com/1")
        self.assertGreater(results[0]["score"], results[1]["score"])


if __name__ == "__main__":
    unittest.main()
