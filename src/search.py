"""Search operations over the inverted index."""

from __future__ import annotations

from typing import Any

from src.indexer import tokenize


def normalise_query(query: str) -> list[str]:
    """Normalise a user query into tokens."""
    return tokenize(query)


def get_word_postings(index_data: dict[str, Any], word: str) -> dict[str, Any]:
    """Return the postings list for a single word."""
    tokens = normalise_query(word)
    if not tokens:
        return {}
    return index_data["index"].get(tokens[0], {})


def find_pages(index_data: dict[str, Any], query: str) -> list[dict[str, Any]]:
    """Return pages that contain all query terms."""
    tokens = normalise_query(query)
    if not tokens:
        return []

    postings_lists = []
    for token in tokens:
        postings = index_data["index"].get(token, {})
        if not postings:
            return []
        postings_lists.append(postings)

    matching_urls = set(postings_lists[0].keys())
    for postings in postings_lists[1:]:
        matching_urls &= set(postings.keys())

    results = []
    for url in sorted(matching_urls):
        total_hits = sum(index_data["index"][token][url]["freq"] for token in tokens)
        results.append(
            {
                "url": url,
                "title": index_data["pages"].get(url, url),
                "score": total_hits,
            }
        )

    return sorted(results, key=lambda item: (-item["score"], item["url"]))
