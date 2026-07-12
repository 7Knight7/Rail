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

export interface ReportResult {
  slug: string;
  status: "success" | "partial_success" | "failed" | "skipped";
  dataset_key?: string | null;
  source_csv_path?: string | null;
  source_row_count?: number | null;
  ingestion_success?: boolean;
  excel_path?: string | null;
  pdf_path?: string | null;
  pdf_download_url?: string | null;
  error?: string | null;
  processing_success?: boolean;
}

export interface AutomationStartResult {
  success: boolean;
  connected: boolean;
  tab_found: boolean;
  url?: string | null;
  title?: string | null;
  error?: string | null;
  error_code?: string | null;
  reports?: ReportResult[];
  stopped_early?: boolean;
  stop_reason?: string | null;
  session_valid?: boolean;
  report_reached?: boolean;
  report_name?: string | null;
  screenshot_path?: string | null;
  report_generated?: boolean;
  filters_applied?: { field: string; value: string }[];
  row_count?: number | null;
  screenshot_before_path?: string | null;
  screenshot_after_path?: string | null;
  download_success?: boolean;
  download_file_path?: string | null;
  download_file_size?: number | null;
  download_error?: string | null;
  ingestion_success?: boolean;
  ingestion_attempted?: boolean;
  ingestion_source?: string | null;
  ingestion_file_path?: string | null;
  screenshot_before_download_path?: string | null;
  screenshot_after_download_path?: string | null;
  html_extracted?: boolean;
  extracted_data_path?: string | null;
  feedback_extracted?: boolean;
  feedback_csv_path?: string | null;
  pdf_archived?: boolean;
  pdf_archive_path?: string | null;
  pdf_archive_error?: string | null;
  pdf_archive_source?: string | null;
  processing_attempted?: boolean;
  processing_success?: boolean;
  processor_used?: string | null;
  input_row_count?: number | null;
  processed_row_count?: number | null;
  excel_path?: string | null;
  pdf_path?: string | null;
  processing_error?: string | null;
  source_a_path?: string | null;
  source_b_path?: string | null;
  source_a_rows?: number | null;
  source_b_rows?: number | null;
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

  pdfDownloadUrl(reportKey: string): string {
    return `/api/v1/automation/reports/${encodeURIComponent(reportKey)}/pdf`;
  },

  async downloadPdf(reportKey: string): Promise<Blob> {
    const response = await fetch(this.pdfDownloadUrl(reportKey), {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/pdf" },
    });
    if (!response.ok) {
      throw new Error(`PDF download failed for ${reportKey}: ${response.status}`);
    }
    return response.blob();
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
