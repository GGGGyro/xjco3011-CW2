"""Website crawler for the coursework search tool."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlparse

from src import vendor as _vendor  # noqa: F401
import requests
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import RequestException

from src.models import PageContent


def parse_html_document(html: str) -> tuple[str, str, list[str]]:
    """Parse HTML into a title, visible text, and raw links."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style"]):
        element.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = " ".join(soup.get_text(" ", strip=True).split())
    links = [anchor["href"] for anchor in soup.find_all("a", href=True)]
    return title, text, links


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
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "XJCO3011 Search Tool"})

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
            except (RequestException, ValueError) as exc:
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
        title, text, _ = parse_html_document(body)
        return PageContent(url=url, title=title or url, text=text)

    def fetch_raw_html(self, url: str) -> str:
        """Fetch raw HTML content while respecting the politeness delay."""
        self._respect_politeness_delay()
        response = self.fetch_response(url)
        self._last_request_time = self.time_fn()
        return response.text

    def fetch_response(self, url: str) -> Response:
        """Fetch an HTTP response object and fail on bad status codes."""
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response

    def extract_links(self, current_url: str, text: str) -> list[str]:
        """Link extraction is overridden or mocked in tests for the base crawler."""
        del current_url
        del text
        return []

    def parse_html(self, html: str) -> tuple[str, str, list[str]]:
        """Parse HTML into title, text, and links."""
        return parse_html_document(html)

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
        response = getattr(exc, "response", None)
        if response is not None and getattr(response, "status_code", None) is not None:
            return f"{url}: HTTP {response.status_code}"
        if isinstance(exc, RequestException):
            return f"{url}: Request error ({exc})"
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
            except (RequestException, ValueError) as exc:
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
