import { apiRequest, API_BASE } from "./client";

export type ActivityStatus = "success" | "error" | "warning" | "info";

export interface ActivityEntry {
  id: string;
  user_id: string;
  action: string;
  message: string;
  status: ActivityStatus;
  report_slug: string | null;
  run_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ActivityListResponse {
  items: ActivityEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface ActivityRecentResponse {
  items: ActivityEntry[];
}

export interface ActivityListParams {
  limit?: number;
  offset?: number;
  status?: string;
  report_slug?: string;
  from?: string;
  to?: string;
}

function buildQuery(params: ActivityListParams): string {
  const search = new URLSearchParams();
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));
  if (params.status) search.set("status", params.status);
  if (params.report_slug) search.set("report_slug", params.report_slug);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const q = search.toString();
  return q ? `?${q}` : "";
}

const openStreams = new Set<EventSource>();

export function closeAllActivityStreams(): void {
  for (const source of openStreams) {
    source.close();
  }
  openStreams.clear();
}

export function openActivityStream(options?: {
  afterId?: string;
  onEvent?: (entry: ActivityEntry) => void;
  onError?: (error: Event) => void;
}): EventSource {
  const params = new URLSearchParams();
  if (options?.afterId) {
    params.set("after_id", options.afterId);
  }
  const qs = params.toString();
  const url = `${API_BASE}/activity/stream${qs ? `?${qs}` : ""}`;
  const source = new EventSource(url, { withCredentials: true });
  openStreams.add(source);

  source.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as ActivityEntry;
      options?.onEvent?.(data);
    } catch {
      // ignore malformed payloads
    }
  };

  source.onerror = (error) => {
    options?.onError?.(error);
  };

  const originalClose = source.close.bind(source);
  source.close = () => {
    openStreams.delete(source);
    originalClose();
  };

  return source;
}

export const activityApi = {
  list(params: ActivityListParams = {}): Promise<ActivityListResponse> {
    return apiRequest<ActivityListResponse>(`/activity${buildQuery(params)}`);
  },

  recent(limit = 10): Promise<ActivityRecentResponse> {
    return apiRequest<ActivityRecentResponse>(`/activity/recent?limit=${limit}`);
  },
};
