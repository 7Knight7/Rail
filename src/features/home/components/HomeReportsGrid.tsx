import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, BarChart3, Building2, MapPin, Train } from "lucide-react";
import { Card, CardBody } from "@/components/ui/Card";
import { cn } from "@/utils/cn";
import type { HomeReportStatus } from "@/api/home";

const REPORT_ICONS: Record<string, LucideIcon> = {
  merging: MapPin,
  division: Building2,
  "train-no": Train,
  types: BarChart3,
  "scr-train": Train,
  "scr-station": Building2,
};

interface HomeReportsGridProps {
  reports: HomeReportStatus[];
  loading?: boolean;
}

export function HomeReportsGrid({ reports, loading }: HomeReportsGridProps) {
  const generatedCount = reports.filter((report) => report.status === "Generated").length;

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-rail-ink">Today&apos;s Reports</h2>
        <p className="mt-1 text-sm text-rail-muted">
          {loading
            ? "Loading report status..."
            : `${generatedCount} of ${reports.length} reports generated today`}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {loading ? (
          <p className="col-span-full text-sm text-rail-muted">Loading reports...</p>
        ) : (
          reports.map((report) => {
            const Icon = REPORT_ICONS[report.reportId] ?? BarChart3;
            return (
              <Link key={report.reportId} to={report.path} className="group block">
                <Card className="h-full hover:-translate-y-0.5 hover:shadow-premium">
                  <CardBody className="p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 transition-colors group-hover:bg-primary/15">
                        <Icon className="h-5 w-5 text-primary" strokeWidth={1.75} />
                      </div>
                      <ArrowUpRight className="h-4 w-4 text-rail-muted opacity-0 transition-all duration-200 group-hover:opacity-100" />
                    </div>
                    <p className="mt-4 font-medium text-rail-ink">{report.name}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-xs text-rail-muted">
                        {report.generatedAt
                          ? new Date(report.generatedAt).toLocaleString()
                          : "Not generated yet"}
                      </span>
                      <span
                        className={cn(
                          "status-pill",
                          report.status === "Generated"
                            ? "bg-success-muted text-success"
                            : "bg-surface text-rail-muted",
                        )}
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-current opacity-60" />
                        {report.status}
                      </span>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            );
          })
        )}
      </div>
    </section>
  );
}
