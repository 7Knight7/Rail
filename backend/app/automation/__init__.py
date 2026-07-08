"""In-process Playwright automation package."""

from app.automation.browser import BrowserConnectionError, BrowserManager
from app.automation.config import AutomationConfig, config
from app.automation.downloader import ReportDownloader
from app.automation.navigation import NavigationService
from app.automation.reports import ReportCatalog, ReportDefinition
from app.automation.run import run
from app.automation.selectors import PortalSelectors, selectors
from app.automation.session import SessionManager

__all__ = [
    "AutomationConfig",
    "BrowserConnectionError",
    "BrowserManager",
    "NavigationService",
    "PortalSelectors",
    "ReportCatalog",
    "ReportDefinition",
    "ReportDownloader",
    "SessionManager",
    "config",
    "run",
    "selectors",
]
