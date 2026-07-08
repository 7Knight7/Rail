"""Browser session and tab management via CDP attach."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Browser, Page

from app.automation.utils import ensure_directory, normalize_url
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class RailMadadTabNotFoundError(AppException):
    """Raised when no open tab matches the RailMadad portal URL."""

    def __init__(self, message: str = "RailMadad tab not found among open tabs") -> None:
        super().__init__(message=message, code="RAILMADAD_TAB_NOT_FOUND")


@dataclass(frozen=True)
class TabInfo:
    """Metadata for a single browser tab discovered over CDP."""

    context_index: int
    tab_index: int
    url: str
    title: str
    is_railmadad: bool
    page: Page

    def format_line(self) -> str:
        label = " (RailMadad)" if self.is_railmadad else ""
        return f"[ctx={self.context_index} tab={self.tab_index}] {self.url}{label}"


@dataclass
class AttachResult:
    """Outcome of a CDP attach and tab-discovery run."""

    success: bool
    tabs: list[TabInfo]
    railmadad_tab: TabInfo | None = None
    screenshot_path: str | None = None
    error: str | None = None


class SessionManager:
    """Tracks the active browser session and RailMadad page."""

    def __init__(
        self,
        browser: Browser | None = None,
        railmadad_url: str = "https://railmadad.indianrail.gov.in",
    ) -> None:
        self._browser = browser
        self._page: Page | None = None
        self._railmadad_url = railmadad_url
        self._tabs: list[TabInfo] = []

    @property
    def browser(self) -> Browser | None:
        return self._browser

    @property
    def page(self) -> Page | None:
        return self._page

    @property
    def tabs(self) -> list[TabInfo]:
        return list(self._tabs)

    def bind_browser(self, browser: Browser) -> None:
        """Associate a connected browser with this session."""
        self._browser = browser

    def bind_page(self, page: Page) -> None:
        """Set the active RailMadad page."""
        self._page = page

    @staticmethod
    def is_railmadad_url(page_url: str, base_url: str) -> bool:
        """Return True if page_url belongs to the RailMadad portal."""
        if not page_url or page_url in ("about:blank", "chrome://newtab/"):
            return False

        normalized_page = normalize_url(page_url)
        normalized_base = normalize_url(base_url)

        if normalized_page.startswith(normalized_base):
            return True

        host = urlparse(page_url).netloc.lower()
        return "railmadad" in host

    async def discover_tabs(self, browser: Browser) -> list[TabInfo]:
        """Enumerate all browser contexts and open tabs."""
        self.bind_browser(browser)
        tabs: list[TabInfo] = []

        contexts = browser.contexts
        logger.info("Discovered %d browser context(s)", len(contexts))

        for context_index, context in enumerate(contexts):
            pages = context.pages
            for tab_index, page in enumerate(pages):
                url = page.url
                try:
                    title = await page.title()
                except Exception:
                    title = ""

                is_railmadad = self.is_railmadad_url(url, self._railmadad_url)
                tab = TabInfo(
                    context_index=context_index,
                    tab_index=tab_index,
                    url=url,
                    title=title,
                    is_railmadad=is_railmadad,
                    page=page,
                )
                tabs.append(tab)

        self._tabs = tabs
        logger.info("Discovered %d open tab(s) across %d context(s)", len(tabs), len(contexts))
        return tabs

    @staticmethod
    def _tab_priority(tab: TabInfo, prefer_url_fragment: str | None = None) -> int:
        """Score RailMadad tabs — higher is preferred for automation attach."""
        url = tab.url.lower()
        if prefer_url_fragment and prefer_url_fragment.lower() in url:
            return 200
        if "mis_reports" in url:
            return 100
        if "/rmmis/admin" in url:
            return 80
        if "/madad/final" in url:
            return 10
        return 50

    def find_railmadad_tab(
        self,
        tabs: list[TabInfo] | None = None,
        prefer_url_fragment: str | None = None,
    ) -> TabInfo | None:
        """Return the best RailMadad tab, preferring admin MIS report pages."""
        source = tabs if tabs is not None else self._tabs
        railmadad_tabs = [tab for tab in source if tab.is_railmadad]
        if not railmadad_tabs:
            return None
        return max(
            railmadad_tabs,
            key=lambda tab: self._tab_priority(tab, prefer_url_fragment),
        )

    async def activate_tab(self, page: Page) -> None:
        """Bring an existing tab to the foreground without navigation."""
        await page.bring_to_front()
        self.bind_page(page)

    async def capture_screenshot(self, page: Page, dest_dir: Path) -> str:
        """Capture a full-page screenshot and return the saved file path."""
        directory = ensure_directory(dest_dir)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        path = directory / f"failure_{timestamp}.png"
        await page.screenshot(path=str(path), full_page=True)
        logger.info("Failure screenshot saved to %s", path)
        return str(path)

    def first_available_page(self, tabs: list[TabInfo] | None = None) -> Page | None:
        """Return the first page from discovered tabs, if any."""
        source = tabs if tabs is not None else self._tabs
        if not source:
            return None
        return source[0].page
