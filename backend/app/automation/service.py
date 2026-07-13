"""In-process browser automation service."""

import asyncio
import logging
import sys
import threading

from app.automation.cancellation import (
    clear_cancel,
    clear_pause,
    request_cancel,
    request_pause,
)
from app.automation.run import attach_to_railmadad
from app.automation.run_registry import create_cdp_run, mark_run_stopped, set_run_status
from app.automation.schemas import MultiReportResult
from app.infrastructure.database.models import AutomationRunModel
from app.infrastructure.database.session import SessionLocal

logger = logging.getLogger(__name__)


def _run_attach_in_thread(
    user_id: str | None = None,
    report_slugs: list[str] | None = None,
    run_id: str | None = None,
) -> MultiReportResult:
    """Run Playwright in a dedicated loop (required on Windows + Uvicorn)."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(
        attach_to_railmadad(user_id=user_id, report_slugs=report_slugs, run_id=run_id)
    )


class AutomationService:
    """Single entry point for in-process Playwright automation."""

    async def start(
        self,
        user_id: str | None = None,
        report_slugs: list[str] | None = None,
    ) -> MultiReportResult:
        """Connect to Chrome via CDP and run catalog reports (blocking until done)."""
        return await asyncio.to_thread(_run_attach_in_thread, user_id, report_slugs, None)

    async def start_async(
        self,
        user_id: str | None = None,
        report_slugs: list[str] | None = None,
    ) -> tuple[str, str]:
        """Create a run row and start CDP work in a background thread.

        Returns (run_id, status) immediately so the UI can poll GET /runs/{id}.
        """
        async with SessionLocal() as db:
            run = await create_cdp_run(db, user_id=user_id)
            run_id = run.id

        clear_cancel(run_id)
        clear_pause(run_id)

        def _worker() -> None:
            try:
                _run_attach_in_thread(user_id, report_slugs, run_id)
            except Exception:
                logger.exception("Background automation failed for run %s", run_id)
            finally:
                clear_cancel(run_id)
                clear_pause(run_id)

        thread = threading.Thread(
            target=_worker,
            name=f"automation-{run_id[:8]}",
            daemon=True,
        )
        thread.start()
        return run_id, "running"

    async def stop(
        self,
        run_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, str | bool]:
        """Request cooperative cancel and mark the CDP run stopped."""
        async with SessionLocal() as db:
            run = await db.get(AutomationRunModel, run_id)
            if not run:
                return {
                    "success": False,
                    "status": "not_found",
                    "message": "Run not found",
                    "run_id": run_id,
                }
            if run.status in {"completed", "failed", "stopped"}:
                return {
                    "success": True,
                    "status": run.status,
                    "message": f"Run already {run.status}",
                    "run_id": run_id,
                }

            request_cancel(run_id)
            clear_pause(run_id)
            await mark_run_stopped(
                db, run_id, user_id=user_id, intermediate=True
            )
            # Immediately surface terminal stopped for UI; worker finalizes details.
            await mark_run_stopped(db, run_id, user_id=user_id, intermediate=False)
            logger.info("cdp_run_stop_requested run_id=%s", run_id)
            return {
                "success": True,
                "status": "stopped",
                "message": "Automation stopped",
                "run_id": run_id,
            }

    async def pause(
        self,
        run_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, str | bool]:
        async with SessionLocal() as db:
            run = await db.get(AutomationRunModel, run_id)
            if not run:
                return {
                    "success": False,
                    "status": "not_found",
                    "message": "Run not found",
                    "run_id": run_id,
                }
            if run.status in {"completed", "failed", "stopped"}:
                return {
                    "success": False,
                    "status": run.status,
                    "message": f"Run already {run.status}",
                    "run_id": run_id,
                }
            if run.status == "paused":
                return {
                    "success": True,
                    "status": "paused",
                    "message": "Run already paused",
                    "run_id": run_id,
                }

            request_pause(run_id)
            await set_run_status(
                db,
                run_id,
                "pause_requested",
                user_id=user_id,
                activity_action="AUTOMATION_PAUSE_REQUESTED",
                activity_message="Report generation pause requested",
            )
            logger.info("cdp_run_pause_requested run_id=%s", run_id)
            return {
                "success": True,
                "status": "pause_requested",
                "message": "Pause requested",
                "run_id": run_id,
            }

    async def resume(
        self,
        run_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, str | bool]:
        async with SessionLocal() as db:
            run = await db.get(AutomationRunModel, run_id)
            if not run:
                return {
                    "success": False,
                    "status": "not_found",
                    "message": "Run not found",
                    "run_id": run_id,
                }
            if run.status not in {"paused", "pause_requested", "running"}:
                return {
                    "success": False,
                    "status": run.status,
                    "message": f"Cannot resume from {run.status}",
                    "run_id": run_id,
                }

            clear_pause(run_id)
            await set_run_status(
                db,
                run_id,
                "running",
                user_id=user_id,
                activity_action="AUTOMATION_RESUMED",
                activity_message="Report generation resumed",
            )
            logger.info("cdp_run_resumed run_id=%s", run_id)
            return {
                "success": True,
                "status": "running",
                "message": "Automation resumed",
                "run_id": run_id,
            }
