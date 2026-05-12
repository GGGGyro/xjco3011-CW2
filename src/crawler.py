"""Website crawler for the coursework search tool."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from src.models import PageContent


class QuoteHTMLParser(HTMLParser):
    """Extracts page text, title, and links from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._in_title:
            self.title = cleaned
        self.text_parts.append(cleaned)


@dataclass(slots=True)
class CrawlResult:
    """Stores crawler output and any request failures."""

    pages: list[PageContent]
    errors: list[str]
    pages_crawled: int
    pages_discovered: int


class Crawler:
    """Crawls pages from a single website while respecting a politeness delay."""

    def __init__(
        self,
        base_url: str,
        politeness_delay: float = 6.0,
        max_pages: int | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.base_netloc = urlparse(self.base_url).netloc
        self.politeness_delay = politeness_delay
        self.max_pages = max_pages
        self.sleep_fn = sleep_fn or time.sleep
        self.time_fn = time_fn or time.monotonic
        self._last_request_time: float | None = None
        self._discovered_urls: set[str] = {self.base_url}

    def crawl(self) -> CrawlResult:
        """Crawl all reachable in-domain pages starting from base_url."""
        queue: deque[str] = deque([self.base_url])
        visited: set[str] = set()
        pages: list[PageContent] = []
        errors: list[str] = []

        while queue:
            if self.max_pages is not None and len(pages) >= self.max_pages:
                break
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                page = self.fetch_page(url)
            except (HTTPError, URLError, ValueError) as exc:
                errors.append(self.format_error(url, exc))
                continue

            pages.append(page)

            for raw_link in self.extract_links(page.url, page.text):
                normalised = self.normalise_url(page.url, raw_link)
                if normalised and normalised not in self._discovered_urls:
                    self._discovered_urls.add(normalised)
                    queue.append(normalised)

        return CrawlResult(
            pages=pages,
            errors=errors,
            pages_crawled=len(pages),
            pages_discovered=len(self._discovered_urls),
        )

    def fetch_page(self, url: str) -> PageContent:
        """Fetch a page, applying the configured politeness delay first."""
        body = self.fetch_raw_html(url)
        parser = QuoteHTMLParser()
        parser.feed(body)
        text = " ".join(parser.text_parts)
        title = parser.title or url
        return PageContent(url=url, title=title, text=text)

    def fetch_raw_html(self, url: str) -> str:
        """Fetch raw HTML content while respecting the politeness delay."""
        self._respect_politeness_delay()
        request = Request(url, headers={"User-Agent": "XJCO3011 Search Tool"})
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
        self._last_request_time = self.time_fn()
        return body

    def extract_links(self, current_url: str, text: str) -> list[str]:
        """Re-fetch parsing is avoided in tests; this method is overridden or mocked there."""
        del current_url
        del text
        return []

    def parse_html(self, html: str) -> tuple[str, str, list[str]]:
        """Parse HTML into title, text, and links."""
        parser = QuoteHTMLParser()
        parser.feed(html)
        text = " ".join(parser.text_parts)
        return parser.title, text, parser.links

    def fetch_page_html(self, url: str) -> tuple[PageContent, list[str]]:
        """Fetch a page and return both parsed page content and discovered links."""
        body = self.fetch_raw_html(url)
        title, text, links = self.parse_html(body)
        page = PageContent(url=url, title=title or url, text=text)
        return page, links

    def normalise_url(self, current_url: str, raw_link: str) -> str | None:
        """Convert a raw link into a clean absolute in-domain URL."""
        absolute = urljoin(current_url, raw_link)
        absolute, _ = urldefrag(absolute)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            return None
        if parsed.netloc != self.base_netloc:
            return None
        path = parsed.path or "/"
        if not path.endswith("/") and "." not in path.rsplit("/", maxsplit=1)[-1]:
            path = path + "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _respect_politeness_delay(self) -> None:
        if self._last_request_time is None:
            return
        elapsed = self.time_fn() - self._last_request_time
        remaining = self.politeness_delay - elapsed
        if remaining > 0:
            self.sleep_fn(remaining)

    @staticmethod
    def format_error(url: str, exc: Exception) -> str:
        """Create a more informative crawl error message."""
        if isinstance(exc, HTTPError):
            return f"{url}: HTTP {exc.code}"
        if isinstance(exc, URLError):
            reason = getattr(exc, "reason", exc)
            return f"{url}: URL error ({reason})"
        return f"{url}: {exc}"


class SiteCrawler(Crawler):
    """Concrete crawler that follows in-domain links parsed from HTML."""

    def crawl(self) -> CrawlResult:
        queue: deque[str] = deque([self.base_url])
        visited: set[str] = set()
        pages: list[PageContent] = []
        errors: list[str] = []

        while queue:
            if self.max_pages is not None and len(pages) >= self.max_pages:
                break
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                page, links = self.fetch_page_html(url)
            except (HTTPError, URLError, ValueError) as exc:
                errors.append(self.format_error(url, exc))
                continue

            pages.append(page)

            for raw_link in links:
                normalised = self.normalise_url(page.url, raw_link)
                if normalised and normalised not in self._discovered_urls:
                    self._discovered_urls.add(normalised)
                    queue.append(normalised)

        return CrawlResult(
            pages=pages,
            errors=errors,
            pages_crawled=len(pages),
            pages_discovered=len(self._discovered_urls),
        )
