"""Tests for crawler behaviour."""

from __future__ import annotations

import unittest
from urllib.error import HTTPError, URLError

from src.crawler import Crawler, QuoteHTMLParser, SiteCrawler
from src.models import PageContent


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.current += seconds


class StubCrawler(SiteCrawler):
    def __init__(self, pages: dict[str, tuple[PageContent, list[str]]], **kwargs) -> None:
        super().__init__("https://quotes.toscrape.com/", **kwargs)
        self.pages = pages

    def fetch_page_html(self, url: str) -> tuple[PageContent, list[str]]:
        self._respect_politeness_delay()
        page, links = self.pages[url]
        self._last_request_time = self.time_fn()
        return page, links


class CrawlerTests(unittest.TestCase):
    def test_html_parser_extracts_title_text_and_links(self) -> None:
        parser = QuoteHTMLParser()
        parser.feed(
            """
            <html>
              <head><title>Example Page</title></head>
              <body>
                <p>Hello <strong>world</strong></p>
                <a href="/page/2/">Next</a>
              </body>
            </html>
            """
        )

        self.assertEqual(parser.title, "Example Page")
        self.assertIn("/page/2/", parser.links)
        self.assertIn("Hello", parser.text_parts)
        self.assertIn("world", parser.text_parts)

    def test_normalise_url_keeps_only_in_domain_links(self) -> None:
        crawler = SiteCrawler("https://quotes.toscrape.com/")

        self.assertEqual(
            crawler.normalise_url("https://quotes.toscrape.com/", "/page/2/"),
            "https://quotes.toscrape.com/page/2/",
        )
        self.assertIsNone(
            crawler.normalise_url("https://quotes.toscrape.com/", "https://example.com/")
        )

    def test_crawl_visits_each_page_once_and_respects_delay(self) -> None:
        clock = FakeClock()
        pages = {
            "https://quotes.toscrape.com/": (
                PageContent("https://quotes.toscrape.com/", "Home", "alpha beta"),
                ["/page/2/", "/page/2/"],
            ),
            "https://quotes.toscrape.com/page/2/": (
                PageContent("https://quotes.toscrape.com/page/2/", "Page 2", "beta gamma"),
                ["/"],
            ),
        }
        crawler = StubCrawler(pages, politeness_delay=6.0, sleep_fn=clock.sleep, time_fn=clock.now)

        result = crawler.crawl()

        self.assertEqual(len(result.pages), 2)
        self.assertEqual(result.errors, [])
        self.assertGreaterEqual(clock.current, 6.0)
        self.assertEqual(result.pages_crawled, 2)
        self.assertEqual(result.pages_discovered, 2)

    def test_crawl_respects_max_pages_limit(self) -> None:
        pages = {
            "https://quotes.toscrape.com/": (
                PageContent("https://quotes.toscrape.com/", "Home", "alpha beta"),
                ["/page/2/", "/page/3/"],
            ),
            "https://quotes.toscrape.com/page/2/": (
                PageContent("https://quotes.toscrape.com/page/2/", "Page 2", "beta gamma"),
                [],
            ),
            "https://quotes.toscrape.com/page/3/": (
                PageContent("https://quotes.toscrape.com/page/3/", "Page 3", "gamma delta"),
                [],
            ),
        }
        crawler = StubCrawler(pages, max_pages=2)

        result = crawler.crawl()

        self.assertEqual(result.pages_crawled, 2)
        self.assertEqual(result.pages_discovered, 3)

    def test_fetch_page_uses_fetch_raw_html_hook(self) -> None:
        class FakeCrawler(Crawler):
            def __init__(self) -> None:
                super().__init__("https://quotes.toscrape.com/")

            def fetch_raw_html(self, url: str) -> str:
                self.captured_url = url
                return "<html><head><title>Mock</title></head><body>Hello world</body></html>"

        crawler = FakeCrawler()
        page = crawler.fetch_page("https://quotes.toscrape.com/page/1/")

        self.assertEqual(crawler.captured_url, "https://quotes.toscrape.com/page/1/")
        self.assertEqual(page.title, "Mock")
        self.assertIn("Hello", page.text)

    def test_format_error_handles_http_and_url_errors(self) -> None:
        http_error = HTTPError(
            "https://quotes.toscrape.com/page/2/",
            404,
            "Not Found",
            hdrs=None,
            fp=None,
        )
        url_error = URLError("timed out")

        self.assertEqual(
            Crawler.format_error("https://quotes.toscrape.com/page/2/", http_error),
            "https://quotes.toscrape.com/page/2/: HTTP 404",
        )
        self.assertEqual(
            Crawler.format_error("https://quotes.toscrape.com/page/2/", url_error),
            "https://quotes.toscrape.com/page/2/: URL error (timed out)",
        )


if __name__ == "__main__":
    unittest.main()
