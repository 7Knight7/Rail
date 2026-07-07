import type { ReactNode } from "react";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/PageHeader";
import { cn } from "@/utils/cn";

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

const mockBar = (items: { label: string; value: number }[]) => (
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
            style={{ width: `${Math.min(100, (item.value / 1500) * 100)}%` }}
          />
        </div>
      </div>
    ))}
  </div>
);

export function DashboardPage() {
  return (
    <div className="space-y-10">
      <PageHeader
        title="Dashboard"
        description="Complaint analytics and performance insights from today's reports."
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Today's Complaints" value={1284} subtitle="+5% vs yesterday" />
        <MetricCard title="Open Cases" value={89} subtitle="Pending resolution" />
        <MetricCard title="Resolution Rate" value="87%" subtitle="Last 7 days" />
        <MetricCard title="Feedback Score" value="4.1 / 5" subtitle="Average rating" />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <AnalyticsSection title="Complaint Trends">
          {mockBar([
            { label: "Mon", value: 420 },
            { label: "Tue", value: 380 },
            { label: "Wed", value: 510 },
            { label: "Thu", value: 465 },
            { label: "Fri", value: 312 },
          ])}
        </AnalyticsSection>

        <AnalyticsSection title="Complaint Categories">
          {mockBar([
            { label: "Cleanliness", value: 340 },
            { label: "Punctuality", value: 290 },
            { label: "Staff Behaviour", value: 210 },
            { label: "Facilities", value: 180 },
            { label: "Other", value: 95 },
          ])}
        </AnalyticsSection>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <AnalyticsSection title="Top Zones">
          {mockBar([
            { label: "Secunderabad", value: 1250 },
            { label: "Hyderabad", value: 1180 },
            { label: "Vijayawada", value: 1050 },
          ])}
        </AnalyticsSection>

        <AnalyticsSection title="Top Divisions">
          {mockBar([
            { label: "SC", value: 890 },
            { label: "HYB", value: 780 },
            { label: "BZA", value: 650 },
          ])}
        </AnalyticsSection>

        <AnalyticsSection title="Top Trains">
          {mockBar([
            { label: "12759", value: 142 },
            { label: "12723", value: 128 },
            { label: "17229", value: 115 },
          ])}
        </AnalyticsSection>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <AnalyticsSection title="Feedback Analysis">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              { label: "Positive", value: "62%", color: "text-emerald-600" },
              { label: "Negative", value: "18%", color: "text-red-600" },
              { label: "Neutral", value: "20%", color: "text-slate-600" },
              { label: "Responses", value: "432", color: "text-slate-900" },
            ].map((item) => (
              <div key={item.label} className="rounded-lg bg-surface p-4">
                <p className="text-slate-500">{item.label}</p>
                <p className={`mt-1 text-xl font-semibold tracking-tight ${item.color}`}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </AnalyticsSection>

        <AnalyticsSection title="Resolution Statistics">
          <div className="space-y-4 text-sm">
            {[
              { label: "Avg. resolution time", value: "4.2 days" },
              { label: "Resolved today", value: "156" },
              { label: "Escalated", value: "23" },
              { label: "Closed this week", value: "891" },
            ].map((row, i, arr) => (
              <div
                key={row.label}
                className={cn(
                  "flex justify-between py-1",
                  i < arr.length - 1 && "border-b border-rail-line pb-4",
                )}
              >
                <span className="text-slate-600">{row.label}</span>
                <span className="font-medium tabular-nums text-slate-900">{row.value}</span>
              </div>
            ))}
          </div>
        </AnalyticsSection>
      </section>
    </div>
  );
}
