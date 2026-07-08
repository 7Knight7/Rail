"""Browser session and tab management (implemented in Phase 3)."""

from playwright.async_api import Browser, Page


class SessionManager:
    """Tracks the active browser session and RailMadad page."""

    def __init__(self, browser: Browser | None = None) -> None:
        self._browser = browser
        self._page: Page | None = None

    @property
    def browser(self) -> Browser | None:
        return self._browser

    @property
    def page(self) -> Page | None:
        return self._page

    def bind_browser(self, browser: Browser) -> None:
        """Associate a connected browser with this session."""
        self._browser = browser

    def bind_page(self, page: Page) -> None:
        """Set the active RailMadad page."""
        self._page = page
