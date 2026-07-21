"""In-process browser automation configuration from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EDGE_EXECUTABLE_CANDIDATES: tuple[Path, ...] = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)


def resolve_edge_executable(explicit_path: str | None = None) -> Path | None:
    """Return the first existing Microsoft Edge executable path."""
    if explicit_path:
        candidate = Path(explicit_path)
        if candidate.is_file():
            return candidate
    for candidate in EDGE_EXECUTABLE_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


class AutomationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    automation_browser: str = Field(
        default="edge",
        validation_alias=AliasChoices("AUTOMATION_BROWSER"),
        description="Automation browser target (edge)",
    )
    browser_cdp_url: str = Field(
        default="http://127.0.0.1:9222",
        validation_alias=AliasChoices("BROWSER_CDP_URL", "CHROME_DEBUG_URL"),
        description="Chromium DevTools Protocol endpoint for attach mode",
    )
    edge_executable_path: str | None = Field(
        default=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        validation_alias=AliasChoices("EDGE_EXECUTABLE_PATH"),
        description="Path to msedge.exe for automation debugging",
    )
    edge_user_data_dir: str = Field(
        default=r"C:\EdgeDebug",
        validation_alias=AliasChoices("EDGE_USER_DATA_DIR"),
        description="Dedicated Edge profile directory for automation debugging",
    )
    download_folder: str = Field(
        default="downloads",
        description="Directory for downloaded reports",
    )
    timeout: int = Field(
        default=300,
        ge=1,
        description="Operation timeout in seconds",
    )
    retry_count: int = Field(
        default=3,
        ge=0,
        description="Number of retries for failed operations",
    )
    railmadad_url: str = Field(
        default="https://railmadad.indianrail.gov.in",
        description="RailMadad portal base URL",
    )
    screenshots_dir: str = Field(
        default="storage/automation-screenshots",
        description="Directory for automation failure screenshots",
    )
    debug_screenshots_dir: str = Field(
        default="storage/debug",
        description="Directory for Phase 4 debug verification screenshots",
    )
    downloads_dir: str = Field(
        default="storage/downloads/report1",
        validation_alias=AliasChoices("DOWNLOAD_DIR", "DOWNLOADS_DIR"),
        description="Project download directory (never system Downloads folder)",
    )
    filter_interaction_delay_ms: int = Field(
        default=150,
        ge=0,
        description="Delay between filter field interactions in milliseconds",
    )
    date_format: str = Field(
        default="%d/%m/%Y",
        description="strftime format for portal date fields",
    )
    pdf_archive_dir: str = Field(
        default="storage/downloads",
        validation_alias=AliasChoices("PDF_ARCHIVE_DIR"),
        description="Base directory for archived PDFs",
    )
    extracted_data_dir: str = Field(
        default="storage/extracted",
        validation_alias=AliasChoices("EXTRACTED_DATA_DIR"),
        description="Directory for extracted HTML/CSV data",
    )
    output_excel_dir: str = Field(
        default="storage/output/excel",
        validation_alias=AliasChoices("OUTPUT_EXCEL_DIR"),
        description="Directory for processed Excel output",
    )
    output_pdf_dir: str = Field(
        default="storage/output/pdf",
        validation_alias=AliasChoices("OUTPUT_PDF_DIR"),
        description="Directory for processed PDF output",
    )

    @property
    def chrome_debug_url(self) -> str:
        """Backward-compatible alias for browser_cdp_url."""
        return self.browser_cdp_url

    def resolved_edge_executable(self) -> Path | None:
        return resolve_edge_executable(self.edge_executable_path)


config = AutomationConfig()
