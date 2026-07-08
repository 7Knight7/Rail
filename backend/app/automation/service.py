"""In-process browser automation service."""

import asyncio
import sys

from app.automation.run import attach_to_railmadad
from app.automation.schemas import AutomationStartResult


def _run_attach_in_thread() -> AutomationStartResult:
    """Run Playwright in a dedicated loop (required on Windows + Uvicorn)."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(attach_to_railmadad())


class AutomationService:
    """Single entry point for in-process Playwright automation."""

    async def start(self) -> AutomationStartResult:
        """Connect to Chrome via CDP and activate the RailMadad tab."""
        return await asyncio.to_thread(_run_attach_in_thread)
