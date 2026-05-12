"""Search operations over the inverted index."""

from __future__ import annotations

import re
from typing import Any

from src.indexer import tokenize

PHRASE_QUERY_PATTERN = re.compile(r'^"(.*)"$')


def normalise_query(query: str) -> list[str]:
    """Normalise a user query into tokens."""
    return tokenize(query)


def is_phrase_query(query: str) -> bool:
    """Return True when the raw query is wrapped in double quotes."""
    return bool(PHRASE_QUERY_PATTERN.fullmatch(query.strip()))


def extract_query_terms(query: str) -> list[str]:
    """Extract searchable terms from either a phrase query or a plain query."""
    match = PHRASE_QUERY_PATTERN.fullmatch(query.strip())
    if match:
        return normalise_query(match.group(1))
    return normalise_query(query)


def get_word_postings(index_data: dict[str, Any], word: str) -> dict[str, Any]:
    """Return the postings list for a single word."""
    tokens = normalise_query(word)
    if not tokens:
        return {}
    return index_data["index"].get(tokens[0], {})


def find_pages(index_data: dict[str, Any], query: str) -> list[dict[str, Any]]:
    """Return pages that match either a plain multi-word query or a quoted phrase query."""
    tokens = extract_query_terms(query)
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

    if is_phrase_query(query):
        matching_urls = {
            url for url in matching_urls if _page_contains_phrase(index_data, url, tokens)
        }

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


def _page_contains_phrase(index_data: dict[str, Any], url: str, tokens: list[str]) -> bool:
    """Check whether the exact token sequence appears in a page."""
    if len(tokens) == 1:
        return url in index_data["index"].get(tokens[0], {})

    first_positions = index_data["index"][tokens[0]][url]["positions"]
    remaining_position_sets = [
        set(index_data["index"][token][url]["positions"]) for token in tokens[1:]
    ]

    for start in first_positions:
        if all((start + offset) in remaining_position_sets[offset - 1] for offset in range(1, len(tokens))):
            return True
    return False
