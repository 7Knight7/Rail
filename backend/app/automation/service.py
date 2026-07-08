"""In-process browser automation service."""

from app.automation.run import run


class AutomationService:
    """Orchestrates in-process automation workflows."""

    async def start(self) -> None:
        """Start the automation run (connect to Chrome via CDP)."""
        await run()
