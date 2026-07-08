"""Playwright browser connection via Chrome DevTools Protocol."""

import logging
from typing import TYPE_CHECKING

from playwright.async_api import Browser, async_playwright
from playwright.async_api import Error as PlaywrightError

from app.core.exceptions import AppException

if TYPE_CHECKING:
    from playwright.async_api import Playwright

logger = logging.getLogger(__name__)

DEFAULT_CDP_URL = "http://127.0.0.1:9222"


class BrowserConnectionError(AppException):
    """Raised when Playwright cannot start or attach to a Chromium CDP endpoint."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="BROWSER_CONNECTION_ERROR")


class BrowserManager:
    """Manages a Playwright session attached to an existing Chromium browser."""

    def __init__(self, cdp_url: str = DEFAULT_CDP_URL) -> None:
        self._cdp_url = cdp_url
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    @property
    def browser(self) -> Browser | None:
        return self._browser

    async def connect(self) -> Browser:
        """Start Playwright and attach to Chromium over CDP."""
        if self._browser is not None:
            raise BrowserConnectionError("BrowserManager is already connected")

        logger.info("Starting Playwright")
        try:
            self._playwright = await async_playwright().start()
        except PlaywrightError as exc:
            raise BrowserConnectionError(f"Failed to start Playwright: {exc}") from exc
        except Exception as exc:
            raise BrowserConnectionError(f"Failed to start Playwright: {exc}") from exc

        logger.info("Connecting to Chromium via CDP at %s", self._cdp_url)
        try:
            self._browser = await self._playwright.chromium.connect_over_cdp(self._cdp_url)
        except PlaywrightError as exc:
            await self._stop_playwright()
            raise BrowserConnectionError(
                f"Cannot connect to Chromium at {self._cdp_url}. "
                "Is Chrome running with --remote-debugging-port=9222?"
            ) from exc
        except Exception as exc:
            await self._stop_playwright()
            raise BrowserConnectionError(
                f"Cannot connect to Chromium at {self._cdp_url}. "
                "Is Chrome running with --remote-debugging-port=9222?"
            ) from exc

        logger.info(
            "Connected to Chromium (%d contexts)",
            len(self._browser.contexts),
        )
        return self._browser

    async def close(self) -> None:
        """Disconnect from the browser and stop Playwright. Safe to call multiple times."""
        if self._browser is None and self._playwright is None:
            return

        logger.info("Closing browser connection")

        if self._browser is not None:
            try:
                await self._browser.close()
            except PlaywrightError as exc:
                logger.warning("Error closing browser connection: %s", exc)
            except Exception as exc:
                logger.warning("Error closing browser connection: %s", exc)
            finally:
                self._browser = None

        await self._stop_playwright()

    async def _stop_playwright(self) -> None:
        if self._playwright is None:
            return

        try:
            await self._playwright.stop()
        except PlaywrightError as exc:
            logger.warning("Error stopping Playwright: %s", exc)
        except Exception as exc:
            logger.warning("Error stopping Playwright: %s", exc)
        finally:
            self._playwright = None
