import { apiRequest } from "./client";

export interface HomeStatMetric {
  title: string;
  value: string;
  description: string;
}

export interface HomeActivityItem {
  label: string;
  time: string;
}

export interface HomeReportStatus {
  reportId: string;
  name: string;
  path: string;
  status: string;
  generatedAt: string | null;
}

export interface HomeOverviewResponse {
  stats: HomeStatMetric[];
  recentActivity: HomeActivityItem[];
  reports: HomeReportStatus[];
}

export async function fetchHomeOverview(): Promise<HomeOverviewResponse> {
  return apiRequest<HomeOverviewResponse>("/home/overview");
}
