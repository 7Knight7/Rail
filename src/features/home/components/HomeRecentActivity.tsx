import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { RECENT_ACTIVITY } from "@/features/home/homeData";

export function HomeRecentActivity() {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-rail-ink">Recent Activity</h2>
        <p className="mt-1 text-sm text-rail-muted">Yesterday&apos;s report generation</p>
      </div>

      <Card className="hover:shadow-premium">
        <CardHeader className="border-b border-rail-line py-4">
          <CardTitle className="text-sm">Yesterday</CardTitle>
        </CardHeader>
        <CardBody className="divide-y divide-rail-line p-0">
          {RECENT_ACTIVITY.map((item) => (
            <div
              key={item.label}
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
          ))}
        </CardBody>
      </Card>
    </section>
  );
}
