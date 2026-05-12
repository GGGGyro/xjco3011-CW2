"""Tests for keyword and phrase query processing."""

from __future__ import annotations

import unittest

from src.search import find_pages, get_word_postings, is_phrase_query


SAMPLE_INDEX = {
    "index": {
        "good": {
            "https://example.com/1": {"freq": 2, "positions": [0, 3]},
            "https://example.com/2": {"freq": 1, "positions": [4]},
        },
        "friends": {
            "https://example.com/1": {"freq": 1, "positions": [1]},
            "https://example.com/2": {"freq": 1, "positions": [1]},
        },
        "are": {
            "https://example.com/2": {"freq": 1, "positions": [2]},
        },
    },
    "pages": {
        "https://example.com/1": "One",
        "https://example.com/2": "Two",
    },
    "page_word_counts": {
        "https://example.com/1": 5,
        "https://example.com/2": 7,
    },
    "document_count": 2,
}


class SearchTests(unittest.TestCase):
    def test_get_word_postings_returns_matching_entries(self) -> None:
        postings = get_word_postings(SAMPLE_INDEX, "GOOD")
        self.assertEqual(len(postings), 2)

    def test_find_pages_uses_and_semantics(self) -> None:
        results = find_pages(SAMPLE_INDEX, "good friends")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["url"], "https://example.com/1")

    def test_is_phrase_query_detects_quoted_input(self) -> None:
        self.assertTrue(is_phrase_query('"good friends"'))
        self.assertFalse(is_phrase_query("good friends"))

    def test_find_pages_supports_exact_phrase_query(self) -> None:
        results = find_pages(SAMPLE_INDEX, '"good friends"')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "https://example.com/1")

    def test_find_pages_phrase_query_returns_empty_when_words_are_not_adjacent(self) -> None:
        results = find_pages(SAMPLE_INDEX, '"good are"')
        self.assertEqual(results, [])

    def test_find_pages_returns_empty_for_empty_query(self) -> None:
        self.assertEqual(find_pages(SAMPLE_INDEX, ""), [])

    def test_find_pages_returns_empty_for_missing_word(self) -> None:
        self.assertEqual(find_pages(SAMPLE_INDEX, "missing"), [])


if __name__ == "__main__":
    unittest.main()
