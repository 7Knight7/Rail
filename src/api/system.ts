/**
 * System info and maintenance API client (admin only).
 */

import { apiRequest } from "./client";

export interface SystemComponentStatus {
  ok: boolean;
  detail: string | null;
}

export interface SystemInfo {
  app_version: string;
  environment: string;
  backend: SystemComponentStatus;
  database: SystemComponentStatus;
  database_type: string;
  cdp: SystemComponentStatus;
  automation_status: string;
  active_run_id: string | null;
  last_successful_run_at: string | null;
  last_failed_run_at: string | null;
  storage_usage_bytes: number;
}

export interface ClearCacheResult {
  success: boolean;
  cleared: string[];
}

export const systemApi = {
  async info(): Promise<SystemInfo> {
    return apiRequest<SystemInfo>("/system/info");
  },

  async clearCache(): Promise<ClearCacheResult> {
    return apiRequest<ClearCacheResult>("/system/clear-cache", { method: "POST" });
  },
};
