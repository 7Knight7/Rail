import { useCallback, useEffect, useState } from "react";
import {
  fetchGeneratedReports,
  type GeneratedReportItem,
  type GeneratedReportSortField,
  type SortOrder,
} from "@/api/outputs";

interface UseGeneratedReportsResult {
  reports: GeneratedReportItem[];
  loading: boolean;
  error: string | null;
  search: string;
  sortBy: GeneratedReportSortField;
  sortOrder: SortOrder;
  setSearch: (value: string) => void;
  setSortBy: (value: GeneratedReportSortField) => void;
  toggleSortOrder: () => void;
  refresh: () => Promise<void>;
}

export function useGeneratedReports(): UseGeneratedReportsResult {
  const [reports, setReports] = useState<GeneratedReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<GeneratedReportSortField>("generatedAt");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchGeneratedReports({
        search: search.trim() || undefined,
        sortBy,
        sortOrder,
      });
      setReports(response.reports);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load generated reports");
      setReports([]);
    } finally {
      setLoading(false);
    }
  }, [search, sortBy, sortOrder]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const toggleSortOrder = useCallback(() => {
    setSortOrder((current) => (current === "asc" ? "desc" : "asc"));
  }, []);

  return {
    reports,
    loading,
    error,
    search,
    sortBy,
    sortOrder,
    setSearch,
    setSortBy,
    toggleSortOrder,
    refresh,
  };
}
