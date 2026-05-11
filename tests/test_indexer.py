"""Tests for index building."""

from __future__ import annotations

import unittest

from src.indexer import build_index, tokenize
from src.models import PageContent


class IndexerTests(unittest.TestCase):
    def test_tokenize_is_case_insensitive(self) -> None:
        self.assertEqual(tokenize("Good, good FRIENDS!"), ["good", "good", "friends"])

    def test_build_index_stores_frequency_and_positions(self) -> None:
        pages = [
            PageContent("https://example.com/1", "One", "alpha beta alpha"),
            PageContent("https://example.com/2", "Two", "beta gamma"),
        ]

        index_data = build_index(pages)

        alpha_postings = index_data["index"]["alpha"]["https://example.com/1"]
        self.assertEqual(alpha_postings["freq"], 2)
        self.assertEqual(alpha_postings["positions"], [0, 2])
        self.assertEqual(index_data["document_count"], 2)


if __name__ == "__main__":
    unittest.main()
