import { useCallback, useMemo } from "react";
import { useAutomationDashboard } from "@/features/admin/automation/hooks/useAutomationDashboard";
import type { AutomationWorkspaceProps } from "@/features/automation/components/AutomationWorkspace";
import { useAutomationRunState } from "@/features/automation/hooks/useAutomationRunState";
import { computeProgressPercent, getStepStats } from "@/features/automation/utils/display";
import { mergeActivityLogs } from "@/features/automation/utils/mapApiLogs";

export interface UseAutomationPageReturn extends AutomationWorkspaceProps {
  loading: boolean;
  /** Exposed for future Playwright WebSocket / SSE bridge. */
  handlePlaywrightEvent: ReturnType<typeof useAutomationRunState>["handlePlaywrightEvent"];
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
    runNow,
    stop,
    pause,
    resume,
    refresh,
  } = useAutomationDashboard(2000);

  const runState = useAutomationRunState();
  const { state, prepareRun, appendActivityLog, handlePlaywrightEvent } = runState;

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

    prepareRun(state.selectedReportIds);
    appendActivityLog({
      level: "info",
      message: "Report generation started",
      source: "pipeline",
    });

    try {
      await runNow();
    } catch {
      handlePlaywrightEvent({
        type: "run_failed",
        message: "Report generation could not be started",
      });
    }
  }, [
    appendActivityLog,
    handlePlaywrightEvent,
    isBusy,
    prepareRun,
    runNow,
    state.selectedReportIds,
  ]);

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
    onStart,
    onStop,
    onPause,
    onResume,
    onRefresh: refresh,
    onToggleReport: runState.toggleReport,
    onSelectAllReports: runState.selectAllReports,
  };
}
