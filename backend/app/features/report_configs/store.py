"""Persist user report configuration."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.features.processing.schemas import ReportConfiguration


class SaveReportConfigRequest(BaseModel):
    configuration: ReportConfiguration

    model_config = ConfigDict(populate_by_name=True)


class SavedReportConfigResponse(BaseModel):
    report_id: str = Field(alias="reportId")
    configuration: ReportConfiguration
    updated_at: str = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class SavedReportConfigStore:
    def __init__(self) -> None:
        self._base_dir = Path(settings.exports_directory).parent / "saved_configs"
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, user_id: str, report_id: str, configuration: ReportConfiguration) -> SavedReportConfigResponse:
        from datetime import UTC, datetime

        updated_at = datetime.now(UTC).isoformat()
        payload = {
            "reportId": report_id,
            "configuration": configuration.model_dump(by_alias=True),
            "updatedAt": updated_at,
        }
        path = self._path(user_id, report_id)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return SavedReportConfigResponse(
            reportId=report_id,
            configuration=configuration,
            updatedAt=updated_at,
        )

    def load(self, user_id: str, report_id: str) -> SavedReportConfigResponse | None:
        path = self._path(user_id, report_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return SavedReportConfigResponse(
                reportId=report_id,
                configuration=ReportConfiguration.model_validate(payload["configuration"]),
                updatedAt=payload.get("updatedAt", ""),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def _path(self, user_id: str, report_id: str) -> Path:
        safe_user = "".join(char for char in user_id if char.isalnum() or char in "-_")
        return self._base_dir / safe_user / f"{report_id}.json"
