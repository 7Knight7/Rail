import { useCallback, useMemo, useState } from "react";
import { automationApi } from "@/api/automation";
import { useAutomationDashboard } from "@/features/admin/automation/hooks/useAutomationDashboard";
import type { AutomationWorkspaceProps } from "@/features/automation/components/AutomationWorkspace";
import { useAutomationRunState } from "@/features/automation/hooks/useAutomationRunState";
import { computeProgressPercent, getStepStats } from "@/features/automation/utils/display";
import { mergeActivityLogs } from "@/features/automation/utils/mapApiLogs";

export interface UseAutomationPageReturn extends AutomationWorkspaceProps {
  loading: boolean;
  /** Exposed for future Playwright WebSocket / SSE bridge. */
  handlePlaywrightEvent: ReturnType<typeof useAutomationRunState>["handlePlaywrightEvent"];
  /** Whether to show the RailMadad login required dialog. */
  showLoginDialog: boolean;
  /** Close the login dialog. */
  onCloseLoginDialog: () => void;
}

/**
 * Page-level container: API controls + run state.
 * Playwright events should be forwarded to `handlePlaywrightEvent`.
 */
export function useAutomationPage(): UseAutomationPageReturn {
  const {
    loading,
    acting,
    isActive,
    isRunning,
    isPaused,
    logs: apiLogs,
    startInProcess,
    stop,
    pause,
    resume,
    refresh,
  } = useAutomationDashboard(2000);

  const runState = useAutomationRunState();
  const { state, appendActivityLog, handlePlaywrightEvent } = runState;

  const [showLoginDialog, setShowLoginDialog] = useState(false);

  const activityLog = useMemo(
    () => mergeActivityLogs(state.activityLog, apiLogs),
    [state.activityLog, apiLogs],
  );

  const progressPercent = computeProgressPercent(state.steps);
  const stepStats = getStepStats(state.steps);
  const hasFailed = stepStats.failed > 0 || state.runStatus === "failed";
  const isBusy = isActive || state.runStatus === "running" || state.runStatus === "paused";
  const isComplete = state.completionSummary != null && !isBusy;

  const onStart = useCallback(async () => {
    if (state.selectedReportIds.length === 0 || isBusy) return;

    appendActivityLog({
      level: "info",
      message: "Connecting to RailMadad via Playwright…",
      source: "playwright",
    });

    const result = await startInProcess();

    // Check for login required error - show dialog instead of error log
    if (result?.error_code === "RAILMADAD_NOT_LOGGED_IN") {
      setShowLoginDialog(true);
      return;
    }

    if (result?.success) {
      appendActivityLog({
        level: "success",
        message: `RailMadad multi-report run finished (${result.reports?.length ?? 0} reports)`,
        source: "playwright",
      });
      for (const report of result.reports ?? []) {
        appendActivityLog({
          level: report.status === "success" ? "success" : "warning",
          message: `${report.slug}: ${report.status}${report.pdf_download_url ? ` — ${report.pdf_download_url}` : ""}`,
          source: "playwright",
        });
      }
      const downloads = (result.reports ?? [])
        .filter((r) => r.status === "success" && (r.pdf_path || r.pdf_download_url))
        .map((r) => ({
          slug: r.slug,
          datasetKey: r.dataset_key ?? r.slug,
          pdfDownloadUrl: r.pdf_download_url ?? automationApi.pdfDownloadUrl(r.slug),
          status: r.status,
        }));
      handlePlaywrightEvent({
        type: "run_completed",
        summary: {
          reportsGenerated: downloads.length || (result.reports?.length ?? 0),
          dashboardUpdated: true,
          analyticsRefreshed: true,
          pdfsGenerated: downloads.length,
          executionTimeMs: 0,
          reportDownloads: downloads,
        },
      });
      return;
    }

    appendActivityLog({
      level: "error",
      message: result?.error ?? "Playwright could not connect to RailMadad",
      source: "playwright",
    });
  }, [appendActivityLog, handlePlaywrightEvent, isBusy, startInProcess, state.selectedReportIds.length]);

  const onStop = useCallback(async () => {
    try {
      await stop();
      handlePlaywrightEvent({ type: "run_failed", message: "Report generation stopped" });
    } catch {
      appendActivityLog({
        level: "error",
        message: "Failed to stop report generation",
        source: "pipeline",
      });
    }
  }, [appendActivityLog, handlePlaywrightEvent, stop]);

  const onPause = useCallback(async () => {
    try {
      await pause();
      handlePlaywrightEvent({ type: "run_paused" });
    } catch {
      appendActivityLog({
        level: "error",
        message: "Failed to pause report generation",
        source: "pipeline",
      });
    }
  }, [appendActivityLog, handlePlaywrightEvent, pause]);

  const onResume = useCallback(async () => {
    try {
      await resume();
      handlePlaywrightEvent({ type: "run_resumed" });
    } catch {
      appendActivityLog({
        level: "error",
        message: "Failed to resume report generation",
        source: "pipeline",
      });
    }
  }, [appendActivityLog, handlePlaywrightEvent, resume]);

  const onCloseLoginDialog = useCallback(() => {
    setShowLoginDialog(false);
  }, []);

  return {
    loading,
    handlePlaywrightEvent,
    reports: runState.reports,
    selectedReportIds: state.selectedReportIds,
    allSelected: runState.allSelected,
    estimatedMinutes: runState.estimatedMinutes,
    steps: state.steps,
    progressPercent,
    activityLog,
    completionSummary: state.completionSummary,
    runStatus: state.runStatus,
    isBusy,
    isPaused: isPaused || state.runStatus === "paused",
    isRunning: isRunning || state.runStatus === "running",
    isActive,
    acting,
    hasFailed,
    isComplete,
    showLoginDialog,
    onCloseLoginDialog,
    onStart,
    onStop,
    onPause,
    onResume,
    onRefresh: refresh,
    onToggleReport: runState.toggleReport,
    onSelectAllReports: runState.selectAllReports,
  };
}
