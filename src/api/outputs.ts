import { apiRequest } from "./client";
import type { DashboardResponse } from "./dashboard";
import type { ProcessDatasetResponse, ReportConfiguration } from "./processing";

export interface OutputArtifact {
  format: "excel" | "pdf" | "csv" | "dashboard_json";
  filename: string;
  path: string;
  downloadUrl: string;
  size: number;
}

export interface GenerateOutputsRequest {
  reportId: string;
  reportName?: string;
  processed?: ProcessDatasetResponse;
  configuration?: ReportConfiguration;
  includeExcel?: boolean;
  includePdf?: boolean;
  includeCsv?: boolean;
  includeDashboard?: boolean;
  period?: string;
}

export interface GenerateOutputsResponse {
  batchId: string;
  reportId: string;
  reportName: string;
  generatedAt: string;
  processed: ProcessDatasetResponse;
  dashboard: DashboardResponse | null;
  artifacts: OutputArtifact[];
}

export interface GeneratedReportItem {
  batchId: string;
  reportId: string;
  reportName: string;
  reportType: string;
  generatedAt: string;
  status: "completed" | "partial" | "failed";
  excelDownloadUrl: string | null;
  pdfDownloadUrl: string | null;
  excelSize: number | null;
  pdfSize: number | null;
}

export interface GeneratedReportListResponse {
  reports: GeneratedReportItem[];
  total: number;
}

export type GeneratedReportSortField = "reportName" | "reportType" | "generatedAt" | "status";
export type SortOrder = "asc" | "desc";

export async function fetchGeneratedReports(params?: {
  search?: string;
  sortBy?: GeneratedReportSortField;
  sortOrder?: SortOrder;
}): Promise<GeneratedReportListResponse> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.sortBy) query.set("sortBy", params.sortBy);
  if (params?.sortOrder) query.set("sortOrder", params.sortOrder);
  const suffix = query.toString();
  return apiRequest<GeneratedReportListResponse>(`/outputs/reports${suffix ? `?${suffix}` : ""}`);
}

export async function generateOutputs(
  request: GenerateOutputsRequest,
): Promise<GenerateOutputsResponse> {
  return apiRequest<GenerateOutputsResponse>("/outputs/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function getOutputDownloadUrl(
  batchId: string,
  format: "excel" | "pdf" | "csv" | "dashboard",
): string {
  return `/api/v1/outputs/${batchId}/download?format=${format}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
