"""Report download engine (implemented in Phase 5)."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportDownloader:
    """Downloads reports from the portal into local storage."""

    def __init__(self, download_dir: Path) -> None:
        self.download_dir = download_dir

    async def download_reports(self) -> list[Path]:
        """Download configured reports. Business logic added in Phase 5."""
        raise NotImplementedError("Report downloads are not implemented yet")
