"""In-process browser automation configuration from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AutomationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    chrome_debug_url: str = Field(
        default="http://127.0.0.1:9222",
        description="Chrome DevTools Protocol endpoint for attach mode",
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


config = AutomationConfig()
