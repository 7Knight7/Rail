import { ApiError } from "./client";
import { apiRequest } from "./client";
import type { ReportConfiguration } from "./processing";

export interface SavedReportConfigResponse {
  reportId: string;
  configuration: ReportConfiguration;
  updatedAt: string;
}

export async function fetchSavedReportConfig(
  reportId: string,
): Promise<SavedReportConfigResponse | null> {
  try {
    return await apiRequest<SavedReportConfigResponse>(`/report-configs/${reportId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function saveReportConfig(
  reportId: string,
  configuration: ReportConfiguration,
): Promise<SavedReportConfigResponse> {
  return apiRequest<SavedReportConfigResponse>(`/report-configs/${reportId}`, {
    method: "PUT",
    body: JSON.stringify({ configuration }),
  });
}
