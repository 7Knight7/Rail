"""Playwright browser connection via Chromium DevTools Protocol (Microsoft Edge attach)."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx
from playwright.async_api import Browser, async_playwright
from playwright.async_api import Error as PlaywrightError

from app.core.exceptions import AppException

if TYPE_CHECKING:
    from playwright.async_api import Playwright

logger = logging.getLogger(__name__)

DEFAULT_CDP_URL = "http://127.0.0.1:9222"
EDGE_LAUNCH_POLL_ATTEMPTS = 20
EDGE_LAUNCH_POLL_INTERVAL_SECONDS = 0.5

_CDP_MISSING_EDGE_MSG = (
    "Microsoft Edge automation session was not found. "
    "Start Edge with remote debugging on port 9222 using profile C:\\EdgeDebug "
    "(run .\\scripts\\start-edge.ps1)."
)


class BrowserConnectionError(AppException):
    """Raised when Playwright cannot start or attach to a Chromium CDP endpoint."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="BROWSER_CONNECTION_ERROR")


CDP_PROBE_TIMEOUT_SECONDS = 2.0


def cdp_port(cdp_url: str) -> int:
    parsed = urlparse(cdp_url)
    return parsed.port or 9222


async def fetch_cdp_targets(cdp_url: str = DEFAULT_CDP_URL) -> list[dict[str, Any]]:
    """Return open CDP page targets from GET /json/list."""
    url = cdp_url.rstrip("/") + "/json/list"
    async with httpx.AsyncClient(timeout=CDP_PROBE_TIMEOUT_SECONDS) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


async def probe_cdp_reachable(
    cdp_url: str = DEFAULT_CDP_URL,
    *,
    timeout: float = CDP_PROBE_TIMEOUT_SECONDS,
) -> None:
    """Verify the Edge CDP endpoint responds before starting automation."""
    url = cdp_url.rstrip("/") + "/json/version"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        if response.status_code != 200:
            raise BrowserConnectionError(
                f"Cannot connect to browser CDP at {cdp_url} (HTTP {response.status_code}). "
                f"{_CDP_MISSING_EDGE_MSG}"
            )
    except BrowserConnectionError:
        raise
    except Exception as exc:
        raise BrowserConnectionError(
            f"Cannot connect to browser CDP at {cdp_url}. {_CDP_MISSING_EDGE_MSG}"
        ) from exc


def _close_stale_edge_debug_processes(user_data_dir: str) -> None:
    """Close msedge.exe processes bound to the automation profile (not daily Edge)."""
    if not sys.platform.startswith("win"):
        return
    normalized = user_data_dir.replace("/", "\\")
    ps_filter = normalized.replace("\\", "\\\\")
    command = (
        "Get-CimInstance Win32_Process -Filter \"name='msedge.exe'\" | "
        f"Where-Object {{ $_.CommandLine -like '*{ps_filter}*' }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        logger.info("closed_stale_edge_debug_processes profile=%s", normalized)
    except Exception as exc:
        logger.warning("Could not close stale Edge debug processes: %s", exc)


async def ensure_edge_cdp_ready(
    cdp_url: str = DEFAULT_CDP_URL,
    *,
    auto_launch: bool = True,
    edge_executable: str | None = None,
    user_data_dir: str | None = None,
    startup_url: str | None = None,
) -> None:
    """Ensure Microsoft Edge is listening on the configured CDP port."""
    try:
        await probe_cdp_reachable(cdp_url)
        return
    except BrowserConnectionError:
        if not auto_launch:
            raise

    from app.automation.config import config, resolve_edge_executable

    exe = resolve_edge_executable(edge_executable or config.edge_executable_path)
    if exe is None:
        raise BrowserConnectionError(
            f"Cannot connect to browser CDP at {cdp_url}. "
            "Microsoft Edge (msedge.exe) was not found on this machine. "
            f"{_CDP_MISSING_EDGE_MSG}"
        )

    profile = user_data_dir or config.edge_user_data_dir
    Path(profile).mkdir(parents=True, exist_ok=True)
    port = cdp_port(cdp_url)
    launch_url = startup_url or config.railmadad_url

    _close_stale_edge_debug_processes(profile)
    await asyncio.sleep(1.0)

    args = [
        str(exe),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={profile}",
        launch_url,
    ]

    logger.info(
        "edge_debug_launch_start executable=%s profile=%s port=%d url=%s",
        exe,
        profile,
        port,
        launch_url,
    )
    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )

    for attempt in range(EDGE_LAUNCH_POLL_ATTEMPTS):
        await asyncio.sleep(EDGE_LAUNCH_POLL_INTERVAL_SECONDS)
        try:
            await probe_cdp_reachable(cdp_url)
            logger.info("edge_debug_launch_ready attempt=%d", attempt + 1)
            return
        except BrowserConnectionError:
            continue

    raise BrowserConnectionError(
        f"Cannot connect to browser CDP at {cdp_url} after launching Microsoft Edge. "
        f"{_CDP_MISSING_EDGE_MSG}"
    )


def _log_browser_state(browser: Browser, stage: str) -> None:
    """Log browser context and page counts with URLs for CDP diagnostics."""
    contexts = browser.contexts
    total_pages = sum(len(context.pages) for context in contexts)
    logger.info(
        "CDP browser state [%s]: %d context(s), %d page(s)",
        stage,
        len(contexts),
        total_pages,
    )
    for context_index, context in enumerate(contexts):
        pages = context.pages
        logger.info(
            "CDP browser state [%s]: context=%d has %d page(s)",
            stage,
            context_index,
            len(pages),
        )
        for page_index, page in enumerate(pages):
            logger.info(
                "CDP browser state [%s]: context=%d page=%d url=%s",
                stage,
                context_index,
                page_index,
                page.url,
            )


class BrowserManager:
    """Manages a Playwright session attached to an existing Microsoft Edge browser."""

    def __init__(
        self,
        cdp_url: str = DEFAULT_CDP_URL,
        *,
        auto_launch_edge: bool = True,
    ) -> None:
        self._cdp_url = cdp_url
        self._auto_launch_edge = auto_launch_edge
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    @property
    def browser(self) -> Browser | None:
        return self._browser

    @property
    def cdp_url(self) -> str:
        return self._cdp_url

    def is_browser_connected(self) -> bool:
        """Return True when the Playwright CDP browser handle is still usable."""
        if self._browser is None:
            return False
        try:
            _ = self._browser.contexts
            return True
        except PlaywrightError:
            return False
        except Exception:
            return False

    async def reconnect(self) -> Browser:
        """Drop a dead Playwright session and attach again to the CDP endpoint."""
        logger.info("browser_reconnect_start cdp_url=%s", self._cdp_url)
        await self.close()
        browser = await self.connect()
        logger.info("playwright_driver_started cdp_connected contexts=%d", len(browser.contexts))
        return browser

    async def connect(self) -> Browser:
        """Start Playwright and attach to Microsoft Edge over CDP."""
        if self._browser is not None:
            raise BrowserConnectionError("BrowserManager is already connected")

        await ensure_edge_cdp_ready(self._cdp_url, auto_launch=self._auto_launch_edge)

        logger.info("playwright_driver_started")
        try:
            self._playwright = await async_playwright().start()
        except PlaywrightError as exc:
            cause = exc.__cause__ or exc.__context__
            if isinstance(cause, NotImplementedError):
                logger.exception("Failed to start Playwright (event loop subprocess unsupported)")
                raise BrowserConnectionError(
                    "Failed to start Playwright: event loop does not support subprocesses. "
                    "On Windows, restart the backend; Playwright runs in a worker thread."
                ) from exc
            detail = str(exc).strip() or repr(exc)
            logger.exception("Failed to start Playwright")
            raise BrowserConnectionError(f"Failed to start Playwright: {detail}") from exc
        except NotImplementedError as exc:
            logger.exception("Failed to start Playwright (event loop subprocess unsupported)")
            raise BrowserConnectionError(
                "Failed to start Playwright: event loop does not support subprocesses. "
                "On Windows, restart the backend after updating; Playwright runs in a worker thread."
            ) from exc
        except Exception as exc:
            logger.exception("Failed to start Playwright")
            raise BrowserConnectionError(f"Failed to start Playwright: {exc}") from exc

        logger.info("cdp_connect_start: attaching to Edge via CDP at %s", self._cdp_url)
        try:
            self._browser = await self._playwright.chromium.connect_over_cdp(self._cdp_url)
        except PlaywrightError as exc:
            logger.exception(
                "cdp_connect_failed: cannot attach to browser CDP at %s", self._cdp_url
            )
            await self._stop_playwright()
            raise BrowserConnectionError(
                f"Cannot connect to browser CDP at {self._cdp_url}. {_CDP_MISSING_EDGE_MSG}"
            ) from exc
        except Exception as exc:
            logger.exception(
                "cdp_connect_failed: cannot attach to browser CDP at %s", self._cdp_url
            )
            await self._stop_playwright()
            raise BrowserConnectionError(
                f"Cannot connect to browser CDP at {self._cdp_url}. {_CDP_MISSING_EDGE_MSG}"
            ) from exc

        logger.info(
            "cdp_connected contexts=%d cdp_url=%s",
            len(self._browser.contexts),
            self._cdp_url,
        )
        _log_browser_state(self._browser, "after_connect")
        return self._browser

    async def close(self) -> None:
        """Disconnect Playwright from CDP without closing the user's Edge window."""
        if self._browser is None and self._playwright is None:
            logger.info("cdp_disconnect_skip: no active Playwright or browser session")
            return

        logger.info("Disconnecting Playwright from browser CDP session")

        if self._browser is not None:
            _log_browser_state(self._browser, "before_disconnect")
            logger.info(
                "cdp_disconnect_start: releasing Playwright handle (Edge window stays open)"
            )
            self._browser = None

        if self._playwright is not None:
            logger.info("cdp_disconnect_start: stopping Playwright driver")
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
