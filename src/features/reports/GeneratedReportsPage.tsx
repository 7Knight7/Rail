import { useState } from "react";
import { Download, FileSpreadsheet, Search, ArrowUpDown } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { cn } from "@/utils/cn";
import { formatFileSize, getOutputDownloadUrl } from "@/api/outputs";
import type { GeneratedReportSortField } from "@/api/outputs";
import { useGeneratedReports } from "./hooks/useGeneratedReports";

const STATUS_LABELS = {
  completed: "Completed",
  partial: "Partial",
  failed: "Failed",
} as const;

const SORT_COLUMNS: { id: GeneratedReportSortField; label: string }[] = [
  { id: "reportName", label: "Report Name" },
  { id: "generatedAt", label: "Generated Time" },
  { id: "status", label: "Status" },
  { id: "reportType", label: "Report Type" },
];

function formatGeneratedTime(value: string): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function handleDownload(batchId: string, format: "excel" | "pdf") {
  window.open(getOutputDownloadUrl(batchId, format), "_blank", "noopener,noreferrer");
}

export function GeneratedReportsPage() {
  const { reports, loading, error, search, sortBy, sortOrder, setSearch, setSortBy, toggleSortOrder } =
    useGeneratedReports();
  const [searchInput, setSearchInput] = useState("");

  const handleSearchSubmit = () => {
    setSearch(searchInput);
  };

  const handleSort = (column: GeneratedReportSortField) => {
    if (sortBy === column) {
      toggleSortOrder();
      return;
    }
    setSortBy(column);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Generated Reports"
        description="Your report archive — search and download previously generated documents."
      />

      <Card className="hover:shadow-premium">
        <CardBody className="space-y-4 p-5">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-rail-muted" />
              <Input
                className="h-11 rounded-xl border-rail-line bg-surface pl-10"
                placeholder="Search by report name, type, or status…"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearchSubmit();
                }}
              />
            </div>
            <Button variant="secondary" className="rounded-xl" onClick={handleSearchSubmit}>
              Search
            </Button>
          </div>
        </CardBody>
      </Card>

      {error && (
        <Card>
          <CardBody className="p-5 text-sm text-red-600">{error}</CardBody>
        </Card>
      )}

      <div className="overflow-hidden rounded-2xl border border-rail-line bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-sm">
            <thead className="sticky top-0 z-10 bg-surface/95 backdrop-blur-sm">
              <tr className="border-b border-rail-line">
                {SORT_COLUMNS.map((column) => (
                  <th key={column.id} className="px-5 py-3.5 text-left">
                    <button
                      type="button"
                      onClick={() => handleSort(column.id)}
                      className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-rail-muted transition-colors hover:text-rail-ink"
                    >
                      {column.label}
                      <ArrowUpDown
                        className={cn(
                          "h-3.5 w-3.5",
                          sortBy === column.id ? "text-primary" : "text-rail-muted/60",
                        )}
                      />
                      {sortBy === column.id && (
                        <span className="sr-only">Sorted {sortOrder}</span>
                      )}
                    </button>
                  </th>
                ))}
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wide text-rail-muted">
                  Downloads
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-16 text-center text-sm text-rail-muted">
                    Loading generated reports…
                  </td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-16 text-center text-sm text-rail-muted">
                    {search
                      ? "No reports match your search."
                      : "No generated reports yet. Generate a report from Report Configuration."}
                  </td>
                </tr>
              ) : (
                reports.map((report, index) => (
                  <tr
                    key={report.batchId}
                    className={cn(
                      "border-b border-rail-line/60 transition-colors duration-200 last:border-0",
                      index % 2 === 0 ? "bg-white" : "bg-surface/30",
                      "hover:bg-primary/[0.03]",
                    )}
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                          <FileSpreadsheet className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium text-rail-ink">{report.reportName}</p>
                          {report.excelSize ? (
                            <p className="text-xs text-rail-muted">{formatFileSize(report.excelSize)}</p>
                          ) : null}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-rail-muted">{formatGeneratedTime(report.generatedAt)}</td>
                    <td className="px-5 py-4">
                      <span
                        className={cn(
                          "status-pill",
                          report.status === "completed" && "bg-green-50 text-green-700",
                          report.status === "partial" && "bg-amber-50 text-amber-700",
                          report.status === "failed" && "bg-red-50 text-red-700",
                        )}
                      >
                        {STATUS_LABELS[report.status]}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-rail-muted">{report.reportType}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          className="rounded-xl"
                          disabled={!report.excelDownloadUrl}
                          onClick={() => handleDownload(report.batchId, "excel")}
                        >
                          <Download className="h-3.5 w-3.5" />
                          Excel
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="rounded-xl"
                          disabled={!report.pdfDownloadUrl}
                          onClick={() => handleDownload(report.batchId, "pdf")}
                        >
                          <Download className="h-3.5 w-3.5" />
                          PDF
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
