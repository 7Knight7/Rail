"""Write dashboard JSON artifacts to disk."""

from __future__ import annotations

import json
from pathlib import Path

from app.features.dashboard.schemas import DashboardResponse


class DashboardJsonExporter:
    """Persist dashboard JSON alongside other report outputs."""

    def write(self, dashboard: DashboardResponse, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = dashboard.model_dump(by_alias=True, mode="json")
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path
