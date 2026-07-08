import type { ReactNode } from "react";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/PageHeader";
import { cn } from "@/utils/cn";
import type { ChartDataPoint, DashboardKpi, FeedbackMetric, AnalyticsRow } from "@/api/dashboard";
import { useDashboardData } from "./hooks/useDashboardData";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
}

function MetricCard({ title, value, subtitle }: MetricCardProps) {
  return (
    <Card className="hover:shadow-card">
      <CardBody className="p-6">
        <p className="text-xs font-medium text-slate-500">{title}</p>
        <p className="mt-2 text-3xl font-semibold tracking-tight tabular-nums text-slate-900">
          {value}
        </p>
        {subtitle && <p className="mt-1.5 text-xs text-slate-400">{subtitle}</p>}
      </CardBody>
    </Card>
  );
}

function AnalyticsSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="hover:shadow-card">
      <CardHeader className="pb-1">
        <CardTitle className="text-base font-semibold text-slate-900">{title}</CardTitle>
      </CardHeader>
      <CardBody className="pt-2">{children}</CardBody>
    </Card>
  );
}

function BarChart({ items }: { items: ChartDataPoint[] }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No data available.</p>;
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-1.5 flex justify-between text-sm">
            <span className="text-slate-600">{item.label}</span>
            <span className="font-medium tabular-nums text-slate-900">{item.value}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${item.barWidth}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function KpiGrid({ kpis }: { kpis: DashboardKpi[] }) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi) => (
        <MetricCard key={kpi.title} title={kpi.title} value={kpi.value} subtitle={kpi.subtitle} />
      ))}
    </section>
  );
}

function FeedbackGrid({ items }: { items: FeedbackMetric[] }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No feedback data available.</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-3 text-sm">
      {items.map((item) => (
        <div key={item.label} className="rounded-lg bg-surface p-4">
          <p className="text-slate-500">{item.label}</p>
          <p className={cn("mt-1 text-xl font-semibold tracking-tight", item.color ?? "text-slate-900")}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}

function ResolutionRows({ rows }: { rows: AnalyticsRow[] }) {
  if (!rows.length) {
    return <p className="text-sm text-slate-500">No resolution data available.</p>;
  }

  return (
    <div className="space-y-4 text-sm">
      {rows.map((row, index, arr) => (
        <div
          key={row.label}
          className={cn(
            "flex justify-between py-1",
            index < arr.length - 1 && "border-b border-rail-line pb-4",
          )}
        >
          <span className="text-slate-600">{row.label}</span>
          <span className="font-medium tabular-nums text-slate-900">{row.value}</span>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { data, loading, error } = useDashboardData();

  return (
    <div className="space-y-10">
      <PageHeader
        title="Dashboard"
        description="Complaint analytics and performance insights from today's reports."
      />

      {loading && (
        <Card>
          <CardBody className="p-6 text-sm text-slate-500">Loading dashboard data…</CardBody>
        </Card>
      )}

      {error && (
        <Card>
          <CardBody className="p-6 text-sm text-red-600">{error}</CardBody>
        </Card>
      )}

      {data && (
        <>
          <KpiGrid kpis={data.kpis} />

          <section className="grid gap-6 lg:grid-cols-2">
            <AnalyticsSection title={data.charts.complaintTrends.title}>
              <BarChart items={data.charts.complaintTrends.items} />
            </AnalyticsSection>
            <AnalyticsSection title={data.charts.complaintCategories.title}>
              <BarChart items={data.charts.complaintCategories.items} />
            </AnalyticsSection>
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            <AnalyticsSection title={data.charts.topZones.title}>
              <BarChart items={data.charts.topZones.items} />
            </AnalyticsSection>
            <AnalyticsSection title={data.charts.topDivisions.title}>
              <BarChart items={data.charts.topDivisions.items} />
            </AnalyticsSection>
            <AnalyticsSection title={data.charts.topTrains.title}>
              <BarChart items={data.charts.topTrains.items} />
            </AnalyticsSection>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <AnalyticsSection title="Feedback Analysis">
              <FeedbackGrid items={data.analytics.feedback} />
            </AnalyticsSection>
            <AnalyticsSection title="Resolution Statistics">
              <ResolutionRows rows={data.analytics.resolution} />
            </AnalyticsSection>
          </section>

          {data.recentActivity.length > 0 && (
            <AnalyticsSection title="Recent Activity">
              <div className="space-y-3 text-sm">
                {data.recentActivity.map((item) => (
                  <div key={`${item.label}-${item.time}`} className="flex justify-between">
                    <span className="text-slate-600">{item.label}</span>
                    <span className="text-slate-400">{item.time}</span>
                  </div>
                ))}
              </div>
            </AnalyticsSection>
          )}
        </>
      )}
    </div>
  );
}
