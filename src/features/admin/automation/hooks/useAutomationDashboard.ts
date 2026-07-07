import { useCallback, useEffect, useState } from "react";
import {
  automationApi,
  type AutomationLogEntry,
  type AutomationRunSummary,
  type AutomationStatus,
} from "@/api/automation";
import { useToast } from "@/components/ui/Toast";

export function useAutomationDashboard(pollIntervalMs = 5000) {
  const { showToast } = useToast();
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [history, setHistory] = useState<AutomationRunSummary[]>([]);
  const [logs, setLogs] = useState<AutomationLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [statusRes, historyRes, logsRes] = await Promise.all([
        automationApi.getStatus(),
        automationApi.getHistory(10),
        automationApi.getLogs(),
      ]);
      setStatus(statusRes);
      setHistory(historyRes.runs);
      setLogs(logsRes.logs);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), pollIntervalMs);
    return () => clearInterval(id);
  }, [refresh, pollIntervalMs]);

  const runNow = useCallback(async () => {
    setActing(true);
    try {
      const res = await automationApi.run();
      showToast("success", "Report generation started", res.message);
      await refresh();
    } catch {
      showToast("error", "Failed to start report generation");
    } finally {
      setActing(false);
    }
  }, [refresh, showToast]);

  const stop = useCallback(async () => {
    setActing(true);
    try {
      await automationApi.stop();
      showToast("warning", "Report generation stopped");
      await refresh();
    } catch {
      showToast("error", "Failed to stop");
    } finally {
      setActing(false);
    }
  }, [refresh, showToast]);

  const pause = useCallback(async () => {
    setActing(true);
    try {
      await automationApi.pause();
      showToast("info", "Report generation paused");
      await refresh();
    } catch {
      showToast("error", "Failed to pause");
    } finally {
      setActing(false);
    }
  }, [refresh, showToast]);

  const resume = useCallback(async () => {
    setActing(true);
    try {
      await automationApi.resume();
      showToast("success", "Report generation resumed");
      await refresh();
    } catch {
      showToast("error", "Failed to resume");
    } finally {
      setActing(false);
    }
  }, [refresh, showToast]);

  const isActive = status?.active_run != null;
  const isRunning = status?.active_run?.status === "running";
  const isPaused = status?.is_paused ?? false;

  return {
    status,
    history,
    logs,
    loading,
    acting,
    isActive,
    isRunning,
    isPaused,
    runNow,
    stop,
    pause,
    resume,
    refresh,
  };
}
