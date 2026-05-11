"""Shared data structures for the search tool."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PageContent:
    """Represents the extracted content of a crawled page."""

    url: str
    title: str
    text: str
