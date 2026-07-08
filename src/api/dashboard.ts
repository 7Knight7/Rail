import { apiRequest } from "./client";

export interface DashboardKpi {
  title: string;
  value: string | number;
  subtitle?: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  barWidth: number;
}

export interface ChartSection {
  title: string;
  items: ChartDataPoint[];
}

export interface FeedbackMetric {
  label: string;
  value: string;
  color?: string;
}

export interface AnalyticsRow {
  label: string;
  value: string;
}

export interface RecentActivityItem {
  label: string;
  time: string;
  reportId?: string;
}

export interface DashboardAnalytics {
  feedback: FeedbackMetric[];
  resolution: AnalyticsRow[];
  observations: string[];
}

export interface DashboardCharts {
  complaintTrends: ChartSection;
  complaintCategories: ChartSection;
  topZones: ChartSection;
  topDivisions: ChartSection;
  topTrains: ChartSection;
}

export interface DashboardResponse {
  generatedAt: string;
  period: string;
  kpis: DashboardKpi[];
  charts: DashboardCharts;
  analytics: DashboardAnalytics;
  recentActivity: RecentActivityItem[];
  sourceReports: string[];
  rowCount: number;
}

export interface ProcessedReportInput {
  reportId: string;
  reportName?: string;
  processedAt?: string;
  data: {
    columns: { name: string; index: number }[];
    rows: Record<string, unknown>[];
    highlights: unknown[];
    rowCount: number;
    columnCount: number;
    stepsApplied: string[];
    warnings: string[];
  };
}

export interface DashboardGenerateRequest {
  reports: ProcessedReportInput[];
  period?: string;
}

export async function fetchDashboardOverview(reportIds?: string[]): Promise<DashboardResponse> {
  const params = new URLSearchParams();
  if (reportIds?.length) {
    reportIds.forEach((id) => params.append("reportIds", id));
  }
  const query = params.toString();
  return apiRequest<DashboardResponse>(`/dashboard${query ? `?${query}` : ""}`);
}

export async function generateDashboard(request: DashboardGenerateRequest): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>("/dashboard/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
