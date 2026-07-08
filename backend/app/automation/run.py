"""Smoke-test entrypoint: connect to Chrome via CDP and disconnect cleanly."""

import asyncio
import logging

from app.automation.browser import BrowserConnectionError, BrowserManager
from app.automation.config import config

logger = logging.getLogger(__name__)


async def run() -> bool:
    """Connect to Chrome over CDP, log success, and close Playwright cleanly."""
    manager = BrowserManager(cdp_url=config.chrome_debug_url)
    try:
        await manager.connect()
        logger.info("Connected successfully")
        return True
    finally:
        await manager.close()


async def main() -> None:
    success = await run()
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except BrowserConnectionError:
        raise SystemExit(1) from None
