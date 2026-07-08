/**
 * Automation orchestration API client
 */

import { apiRequest, AUTOMATION_START_TIMEOUT_MS } from "./client";

export interface AutomationRunSummary {
  id: string;
  profile_id: string;
  profile_name: string;
  status: string;
  trigger_type: string;
  success_count: number;
  failure_count: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface AutomationStatus {
  active_run: AutomationRunSummary | null;
  last_run: AutomationRunSummary | null;
  next_scheduled_at: string | null;
  success_rate: number;
  total_runs: number;
  total_failures: number;
  is_paused: boolean;
}

export interface AutomationLogEntry {
  id: string;
  level: string;
  message: string;
  created_at: string;
}

export interface AutomationProfile {
  id: string;
  name: string;
  slug: string;
  portal_url: string;
  username_masked: string;
  download_folder: string;
  browser: string;
  headless: boolean;
  timeout_ms: number;
  retry_count: number;
  delay_seconds: number;
  report_sequence: { name: string; report_path: string; filters: Record<string, unknown> }[];
  is_enabled: boolean;
}

export interface AutomationStartResult {
  success: boolean;
  connected: boolean;
  tab_found: boolean;
  url: string | null;
  title: string | null;
  error?: string | null;
}

export const automationApi = {
  async getStatus(): Promise<AutomationStatus> {
    return apiRequest<AutomationStatus>("/automation/status");
  },

  async getHistory(limit = 20): Promise<{ runs: AutomationRunSummary[]; total: number }> {
    return apiRequest(`/automation/history?limit=${limit}`);
  },

  async getLogs(runId?: string): Promise<{ run_id: string | null; logs: AutomationLogEntry[]; total: number }> {
    const q = runId ? `?run_id=${runId}` : "";
    return apiRequest(`/automation/logs${q}`);
  },

  async run(profileId?: string): Promise<{ run_id: string; status: string; message: string }> {
    return apiRequest("/automation/run", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId ?? null }),
    });
  },

  async start(): Promise<AutomationStartResult> {
    return apiRequest<AutomationStartResult>(
      "/automation/start",
      {
        method: "POST",
        body: JSON.stringify({}),
      },
      false,
      AUTOMATION_START_TIMEOUT_MS,
    );
  },

  async stop(): Promise<{ success: boolean; status: string; message: string }> {
    return apiRequest("/automation/stop", { method: "POST" });
  },

  async pause(): Promise<{ success: boolean; status: string; message: string }> {
    return apiRequest("/automation/pause", { method: "POST" });
  },

  async resume(): Promise<{ success: boolean; status: string; message: string }> {
    return apiRequest("/automation/resume", { method: "POST" });
  },

  async listProfiles(): Promise<{ profiles: AutomationProfile[]; total: number }> {
    return apiRequest("/automation/profiles");
  },
};
