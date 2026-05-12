"""Command-line interface for the coursework search tool."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from src.crawler import SiteCrawler
from src.indexer import build_index
from src.search import find_pages, get_word_postings, is_phrase_query
from src.storage import load_index, save_index

DEFAULT_SITE_URL = "https://quotes.toscrape.com/"
DEFAULT_INDEX_PATH = Path("data") / "quotes_index.json"
DEFAULT_MAX_PAGES = 25


class SearchShell:
    """Small shell exposing the required coursework commands."""

    def __init__(self, site_url: str = DEFAULT_SITE_URL, index_path: Path = DEFAULT_INDEX_PATH) -> None:
        self.site_url = site_url
        self.index_path = index_path
        self.index_data: dict[str, Any] | None = None

    def run_command(self, raw_command: str) -> bool:
        parts = raw_command.strip().split()
        if not parts:
            print("Please enter a command.")
            return True

        command = parts[0].lower()
        args = parts[1:]

        if command == "build":
            self.handle_build()
        elif command == "load":
            self.handle_load()
        elif command == "print":
            self.handle_print(args)
        elif command == "find":
            self.handle_find(args)
        elif command in {"exit", "quit"}:
            return False
        elif command == "help":
            self.print_help()
        else:
            print(f"Unknown command: {command}")
            self.print_help()
        return True

    def handle_build(self) -> None:
        crawler = SiteCrawler(self.site_url, max_pages=DEFAULT_MAX_PAGES)
        result = crawler.crawl()
        if not result.pages:
            print("Build failed: no pages were crawled.")
            if result.errors:
                print("Errors encountered:")
                for error in result.errors:
                    print(f"  - {error}")
            return
        self.index_data = build_index(result.pages)
        save_index(self.index_data, self.index_path)
        print(
            "Built index for "
            f"{result.pages_crawled} pages "
            f"(discovered {result.pages_discovered} unique URLs, limit {DEFAULT_MAX_PAGES})."
        )
        print(f"Saved index to {self.index_path}.")
        if result.errors:
            print("Some pages could not be fetched:")
            for error in result.errors:
                print(f"  - {error}")

    def handle_load(self) -> None:
        if not self.index_path.exists():
            print(f"Index file not found: {self.index_path}")
            return
        self.index_data = load_index(self.index_path)
        print(f"Loaded index from {self.index_path}.")
        print(f"Indexed pages: {self.index_data['document_count']}")

    def handle_print(self, args: list[str]) -> None:
        if not self._ensure_index_loaded():
            return
        if not args:
            print("Usage: print <word>")
            return
        word = args[0]
        postings = get_word_postings(self.index_data, word)
        if not postings:
            print(f"No postings found for '{word}'.")
            return
        print(f"Postings for '{word.lower()}':")
        for url, stats in sorted(postings.items()):
            print(f"- {url}: freq={stats['freq']}, positions={stats['positions']}")

    def handle_find(self, args: list[str]) -> None:
        if not self._ensure_index_loaded():
            return
        if not args:
            print('Usage: find <query terms> or find "exact phrase"')
            return
        query = " ".join(args)
        results = find_pages(self.index_data, query)
        if not results:
            print(f"No pages found for query '{query}'.")
            return
        query_type = "Phrase" if is_phrase_query(query) else "Keyword"
        print(f"{query_type} results for '{query}':")
        for result in results:
            print(f"- {result['title']} ({result['url']}) score={result['score']:.4f}")

    def _ensure_index_loaded(self) -> bool:
        if self.index_data is None:
            print("No index is loaded. Run 'build' or 'load' first.")
            return False
        return True

    @staticmethod
    def print_help() -> None:
        print('Commands: build, load, print <word>, find <query>, find "exact phrase", help, exit')


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    shell = SearchShell()

    if args:
        shell.run_command(" ".join(args))
        return 0

    print("Search tool shell. Type 'help' for commands.")
    while True:
        try:
            raw_command = input("> ")
        except EOFError:
            break
        if not shell.run_command(raw_command):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
