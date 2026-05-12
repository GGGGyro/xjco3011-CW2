"""Tests for command-line shell behaviour."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.main import SearchShell
from src.models import PageContent


class MainTests(unittest.TestCase):
    def test_build_without_limit_uses_full_site_crawl(self) -> None:
        pages = [PageContent("https://example.com", "Example", "alpha beta")]
        crawl_result = {
            "pages": pages,
            "errors": [],
            "pages_crawled": 1,
            "pages_discovered": 1,
        }

        with TemporaryDirectory() as temp_dir:
            shell = SearchShell(index_path=Path(temp_dir) / "index.json")
            stdout = io.StringIO()
            with (
                patch("src.main.SiteCrawler") as crawler_cls,
                redirect_stdout(stdout),
            ):
                crawler_instance = crawler_cls.return_value
                crawler_instance.crawl.return_value.pages = crawl_result["pages"]
                crawler_instance.crawl.return_value.errors = crawl_result["errors"]
                crawler_instance.crawl.return_value.pages_crawled = crawl_result["pages_crawled"]
                crawler_instance.crawl.return_value.pages_discovered = crawl_result["pages_discovered"]

                shell.handle_build([])

            crawler_cls.assert_called_once_with("https://quotes.toscrape.com/", max_pages=None)
            self.assertIn("full-site crawl", stdout.getvalue())

    def test_build_with_limit_passes_max_pages(self) -> None:
        pages = [PageContent("https://example.com", "Example", "alpha beta")]

        with TemporaryDirectory() as temp_dir:
            shell = SearchShell(index_path=Path(temp_dir) / "index.json")
            stdout = io.StringIO()
            with (
                patch("src.main.SiteCrawler") as crawler_cls,
                redirect_stdout(stdout),
            ):
                crawler_instance = crawler_cls.return_value
                crawler_instance.crawl.return_value.pages = pages
                crawler_instance.crawl.return_value.errors = []
                crawler_instance.crawl.return_value.pages_crawled = 1
                crawler_instance.crawl.return_value.pages_discovered = 3

                shell.handle_build(["10"])

            crawler_cls.assert_called_once_with("https://quotes.toscrape.com/", max_pages=10)
            self.assertIn("limit 10", stdout.getvalue())

    def test_build_rejects_invalid_limit(self) -> None:
        shell = SearchShell()
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            shell.handle_build(["abc"])

        self.assertIn("Usage: build [max_pages]", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
