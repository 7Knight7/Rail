import { apiRequest } from "./client";

export interface ProcessedColumn {
  name: string;
  index: number;
}

export interface ProcessDatasetResponse {
  columns: ProcessedColumn[];
  rows: Record<string, unknown>[];
  highlights: {
    rowIndex: number;
    column: string | null;
    backgroundColor: string;
    textColor: string | null;
    bold: boolean;
  }[];
  rowCount: number;
  columnCount: number;
  stepsApplied: string[];
  warnings: string[];
}

export interface FilterConditionConfig {
  column: string;
  operator: string;
  value?: unknown;
  valueTo?: unknown;
  logic?: "AND" | "OR";
}

export interface SortingConfig {
  column: string;
  direction: "asc" | "desc";
  priority?: number;
}

export interface TopNConfig {
  enabled: boolean;
  mode: "top" | "bottom";
  count: number;
  byColumn: string;
}

export interface HighlightConfig {
  column?: string;
  scope?: "cell" | "row" | "column";
  operator?: string;
  value?: unknown;
  backgroundColor?: string;
  textColor?: string;
  bold?: boolean;
  priority?: number;
}

export interface ReportConfiguration {
  filters?: FilterConditionConfig[];
  sorting?: SortingConfig[];
  topN?: TopNConfig;
  hiddenColumns?: string[];
  columnOrder?: string[];
  highlights?: HighlightConfig[];
}

export interface ProcessDatasetRequest {
  reportId?: string;
  filePath?: string;
  configuration?: ReportConfiguration;
}

export async function previewProcessedDataset(
  request: ProcessDatasetRequest,
): Promise<ProcessDatasetResponse> {
  return apiRequest<ProcessDatasetResponse>("/processing/preview", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
