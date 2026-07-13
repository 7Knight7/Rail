"""Run timing spans for profiling full automation runs."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from app.automation.config import config
from app.automation.utils import ensure_directory, log_automation_event
import logging

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class SpanRecord:
    name: str
    started_at: str
    completed_at: str | None = None
    duration_seconds: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportTiming:
    slug: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    extraction_seconds: float | None = None
    processing_seconds: float | None = None
    spans: dict[str, float] = field(default_factory=dict)


@dataclass
class RunTiming:
    """Accumulates wall-clock timings for one full automation run."""

    run_id: str
    started_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None
    total_duration_seconds: float | None = None
    spans: dict[str, float] = field(default_factory=dict)
    reports: dict[str, ReportTiming] = field(default_factory=dict)
    _active: dict[str, float] = field(default_factory=dict, repr=False)

    def start_span(self, name: str) -> None:
        self._active[name] = time.perf_counter()

    def end_span(self, name: str, **meta: Any) -> float:
        start = self._active.pop(name, None)
        if start is None:
            return 0.0
        elapsed = time.perf_counter() - start
        self.spans[name] = round(elapsed, 3)
        log_automation_event(
            logger,
            "timing_span",
            span=name,
            duration_seconds=self.spans[name],
            **meta,
        )
        return elapsed

    @contextmanager
    def span(self, name: str, **meta: Any) -> Iterator[None]:
        self.start_span(name)
        try:
            yield
        finally:
            self.end_span(name, **meta)

    @contextmanager
    def report_span(self, slug: str, span_name: str, **meta: Any) -> Iterator[None]:
        """Record both top-level `span_name:slug` and per-report span maps."""
        full = f"{span_name}:{slug}"
        self.start_span(full)
        try:
            yield
        finally:
            elapsed = self.end_span(full, slug=slug, **meta)
            self.record_report_span(slug, span_name, elapsed)

    def ensure_report(self, slug: str) -> ReportTiming:
        if slug not in self.reports:
            self.reports[slug] = ReportTiming(slug=slug)
        return self.reports[slug]

    def start_report(self, slug: str) -> None:
        rt = self.ensure_report(slug)
        rt.started_at = _now_iso()
        self.start_span(f"report:{slug}")
        log_automation_event(logger, "report_started", slug=slug, run_id=self.run_id)

    def end_report(self, slug: str, **meta: Any) -> None:
        rt = self.ensure_report(slug)
        rt.completed_at = _now_iso()
        elapsed = self.end_span(f"report:{slug}", slug=slug, **meta)
        rt.duration_seconds = round(elapsed, 3)
        log_automation_event(
            logger,
            "report_completed",
            slug=slug,
            run_id=self.run_id,
            duration_seconds=rt.duration_seconds,
            **meta,
        )

    def record_report_span(self, slug: str, span_name: str, seconds: float) -> None:
        rt = self.ensure_report(slug)
        rt.spans[span_name] = round(seconds, 3)
        if span_name == "extraction":
            rt.extraction_seconds = round(seconds, 3)
        elif span_name == "processing":
            rt.processing_seconds = round(seconds, 3)

    def finish(self) -> dict[str, Any]:
        self.completed_at = _now_iso()
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at)
        self.total_duration_seconds = round((end - start).total_seconds(), 3)
        payload = self.to_dict()
        log_automation_event(
            logger,
            "full_run_completed",
            run_id=self.run_id,
            total_duration_seconds=self.total_duration_seconds,
            report_count=len(self.reports),
        )
        self.write_json()
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_seconds": self.total_duration_seconds,
            "spans": dict(self.spans),
            "reports": {
                slug: {
                    "slug": rt.slug,
                    "started_at": rt.started_at,
                    "completed_at": rt.completed_at,
                    "duration_seconds": rt.duration_seconds,
                    "extraction_seconds": rt.extraction_seconds,
                    "processing_seconds": rt.processing_seconds,
                    "spans": dict(rt.spans),
                }
                for slug, rt in self.reports.items()
            },
        }

    def write_json(self) -> Path:
        debug_dir = ensure_directory(Path(config.extracted_data_dir).parent / "debug")
        path = debug_dir / f"run_timing_{self.run_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
