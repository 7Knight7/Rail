import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Card, CardBody } from "@/components/ui/Card";
import { cn } from "@/utils/cn";
import { SCHEDULED_REPORTS } from "@/features/home/homeData";

export function HomeReportsGrid() {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-rail-ink">Today&apos;s Reports</h2>
        <p className="mt-1 text-sm text-rail-muted">Six scheduled reports ready for generation</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {SCHEDULED_REPORTS.map((report) => {
          const Icon = report.icon;
          return (
            <Link key={report.id} to={report.path} className="group block">
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
                    <span className="text-xs text-rail-muted">{report.duration}</span>
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
        })}
      </div>
    </section>
  );
}
