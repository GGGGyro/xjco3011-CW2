"""Index construction utilities."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from src.models import PageContent

WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> list[str]:
    """Split text into case-insensitive word tokens."""
    return [match.group(0).lower() for match in WORD_PATTERN.finditer(text)]


def build_index(pages: list[PageContent]) -> dict[str, Any]:
    """Build an inverted index with per-page frequency and positions."""
    index: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    page_word_counts: dict[str, int] = {}
    titles: dict[str, str] = {}

    for page in pages:
        tokens = tokenize(page.text)
        page_word_counts[page.url] = len(tokens)
        titles[page.url] = page.title
        seen_positions: dict[str, list[int]] = defaultdict(list)

        for position, token in enumerate(tokens):
            seen_positions[token].append(position)

        for token, positions in seen_positions.items():
            index[token][page.url] = {
                "freq": len(positions),
                "positions": positions,
            }

    return {
        "index": dict(index),
        "pages": titles,
        "page_word_counts": page_word_counts,
        "document_count": len(pages),
    }
