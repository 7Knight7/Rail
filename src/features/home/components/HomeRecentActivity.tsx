import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import type { HomeActivityItem } from "@/api/home";

interface HomeRecentActivityProps {
  items: HomeActivityItem[];
  loading?: boolean;
}

export function HomeRecentActivity({ items, loading }: HomeRecentActivityProps) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-rail-ink">Recent Activity</h2>
        <p className="mt-1 text-sm text-rail-muted">Latest report generation events</p>
      </div>

      <Card className="hover:shadow-premium">
        <CardHeader className="border-b border-rail-line py-4">
          <CardTitle className="text-sm">Activity</CardTitle>
        </CardHeader>
        <CardBody className="divide-y divide-rail-line p-0">
          {loading ? (
            <p className="px-6 py-8 text-sm text-rail-muted">Loading activity...</p>
          ) : items.length === 0 ? (
            <p className="px-6 py-8 text-sm text-rail-muted">No recent activity yet.</p>
          ) : (
            items.map((item) => (
              <div
                key={`${item.label}-${item.time}`}
                className="flex items-center justify-between px-6 py-4 transition-colors duration-200 hover:bg-surface"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-success-muted">
                    <span className="h-2 w-2 rounded-full bg-success" />
                  </span>
                  <span className="text-sm font-medium text-rail-ink">{item.label}</span>
                </div>
                <time className="text-xs tabular-nums text-rail-muted">{item.time}</time>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </section>
  );
}
