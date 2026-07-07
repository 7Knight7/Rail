import { useState } from "react";
import { Download, Eye, FileSpreadsheet, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { AUTOMATION_REPORTS } from "@/features/automation/constants";
import { cn } from "@/utils/cn";

type ReportPeriod = "today" | "yesterday" | "previous";

interface ArchiveReport {
  id: string;
  label: string;
  period: ReportPeriod;
  generatedAt: string;
  workflowPath: string;
  size: string;
}

const ARCHIVE: ArchiveReport[] = [
  ...AUTOMATION_REPORTS.map((r) => ({
    id: `${r.id}-today`,
    label: r.label,
    period: "today" as const,
    generatedAt: "Today, 8:42 AM",
    workflowPath: r.workflowPath,
    size: "2.4 MB",
  })),
  ...AUTOMATION_REPORTS.slice(0, 4).map((r) => ({
    id: `${r.id}-yesterday`,
    label: r.label,
    period: "yesterday" as const,
    generatedAt: "Yesterday, 5:42 PM",
    workflowPath: r.workflowPath,
    size: "2.3 MB",
  })),
  ...AUTOMATION_REPORTS.slice(0, 2).map((r) => ({
    id: `${r.id}-prev`,
    label: r.label,
    period: "previous" as const,
    generatedAt: "Mar 28, 2026",
    workflowPath: r.workflowPath,
    size: "2.1 MB",
  })),
];

const PERIOD_LABELS: Record<ReportPeriod, string> = {
  today: "Today",
  yesterday: "Yesterday",
  previous: "Earlier",
};

const PERIOD_TABS = [
  { id: "all" as const, label: "All reports" },
  { id: "today" as const, label: "Today" },
  { id: "yesterday" as const, label: "Yesterday" },
  { id: "previous" as const, label: "Earlier" },
];

export function GeneratedReportsPage() {
  const [search, setSearch] = useState("");
  const [period, setPeriod] = useState<ReportPeriod | "all">("all");

  const filtered = ARCHIVE.filter((r) => {
    const matchesSearch = r.label.toLowerCase().includes(search.toLowerCase());
    const matchesPeriod = period === "all" || r.period === period;
    return matchesSearch && matchesPeriod;
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Generated Reports"
        description="Your report archive — search, preview and download any previously generated document."
      />

      <Card className="hover:shadow-premium">
        <CardBody className="space-y-4 p-5">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-rail-muted" />
            <Input
              className="h-11 rounded-xl border-rail-line bg-surface pl-10"
              placeholder="Search by report name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex flex-wrap gap-1 rounded-xl bg-surface p-1">
            {PERIOD_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setPeriod(tab.id)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm transition-all duration-200",
                  period === tab.id
                    ? "bg-white font-medium text-rail-ink shadow-soft"
                    : "text-rail-muted hover:text-rail-ink",
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      <div className="overflow-hidden rounded-2xl border border-rail-line bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="sticky top-0 z-10 bg-surface/95 backdrop-blur-sm">
              <tr className="border-b border-rail-line">
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wide text-rail-muted">
                  Report
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wide text-rail-muted">
                  Period
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wide text-rail-muted">
                  Generated
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wide text-rail-muted">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-16 text-center text-sm text-rail-muted">
                    No reports match your search.
                  </td>
                </tr>
              ) : (
                filtered.map((report, index) => (
                  <tr
                    key={report.id}
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
                          <p className="font-medium text-rail-ink">{report.label}</p>
                          <p className="text-xs text-rail-muted">{report.size} · Excel</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="status-pill bg-surface text-rail-muted">
                        {PERIOD_LABELS[report.period]}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-rail-muted">{report.generatedAt}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <Button variant="secondary" size="sm" className="rounded-xl" asChild>
                          <Link to={report.workflowPath}>
                            <Eye className="h-3.5 w-3.5" />
                            Preview
                          </Link>
                        </Button>
                        <Button variant="ghost" size="sm" className="rounded-xl" asChild>
                          <Link to={report.workflowPath}>
                            <Download className="h-3.5 w-3.5" />
                            Download
                          </Link>
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
