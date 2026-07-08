"""Portal navigation helpers (implemented in Phase 4)."""

import logging

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class NavigationService:
    """Navigates the RailMadad portal to report pages."""

    async def open_reports_page(self, page: Page) -> None:
        """Open the Reports section. Business logic added in Phase 4."""
        raise NotImplementedError("Reports navigation is not implemented yet")
