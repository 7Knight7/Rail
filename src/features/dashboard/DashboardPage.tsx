import {
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Calendar,
  TrendingUp,
  Activity,
} from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageHeader } from "@/components/PageHeader";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: typeof FileText;
  trend?: string;
  variant?: "default" | "success" | "warning";
}

function StatCard({ title, value, icon: Icon, trend, variant = "default" }: StatCardProps) {
  const bgColors = {
    default: "bg-slate-100",
    success: "bg-green-100",
    warning: "bg-amber-100",
  };
  const iconColors = {
    default: "text-slate-600",
    success: "text-green-600",
    warning: "text-amber-600",
  };

  return (
    <Card>
      <CardBody className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
            {trend && (
              <p className="mt-1 flex items-center gap-1 text-xs text-green-600">
                <TrendingUp className="h-3 w-3" />
                {trend}
              </p>
            )}
          </div>
          <div className={`rounded-lg p-2.5 ${bgColors[variant]}`}>
            <Icon className={`h-5 w-5 ${iconColors[variant]}`} />
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

const mockStats = {
  todayStatus: "Operational",
  reportsGenerated: 47,
  pendingReports: 3,
  lastAutomation: "Today, 14:32",
};

const mockRecentActivity = [
  {
    id: "1",
    action: "Division Report Generated",
    user: "Officer Singh",
    time: "2 minutes ago",
    status: "success" as const,
  },
  {
    id: "2",
    action: "Merging Report Uploaded",
    user: "Officer Kumar",
    time: "15 minutes ago",
    status: "success" as const,
  },
  {
    id: "3",
    action: "SCR Train Analysis Started",
    user: "Officer Reddy",
    time: "1 hour ago",
    status: "pending" as const,
  },
  {
    id: "4",
    action: "Summary Generation Failed",
    user: "System",
    time: "2 hours ago",
    status: "error" as const,
  },
  {
    id: "5",
    action: "Types Report Downloaded",
    user: "Officer Patel",
    time: "3 hours ago",
    status: "success" as const,
  },
];

const mockQuickActions = [
  { label: "Generate Merging Report", path: "/workflows/merging" },
  { label: "Generate Division Report", path: "/workflows/division" },
  { label: "Generate Summary", path: "/workflows/summary" },
];

export function DashboardPage() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of railway report generation and system status"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Today's Status"
          value={mockStats.todayStatus}
          icon={Activity}
          variant="success"
        />
        <StatCard
          title="Reports Generated"
          value={mockStats.reportsGenerated}
          icon={FileText}
          trend="+12% from yesterday"
        />
        <StatCard
          title="Pending Reports"
          value={mockStats.pendingReports}
          icon={Clock}
          variant={mockStats.pendingReports > 5 ? "warning" : "default"}
        />
        <StatCard
          title="Last Automation Run"
          value={mockStats.lastAutomation}
          icon={Calendar}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-slate-500" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {mockRecentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center gap-4 border-b border-slate-100 pb-4 last:border-0 last:pb-0"
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      activity.status === "success"
                        ? "bg-green-100"
                        : activity.status === "error"
                          ? "bg-red-100"
                          : "bg-amber-100"
                    }`}
                  >
                    {activity.status === "success" ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : activity.status === "error" ? (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    ) : (
                      <Clock className="h-4 w-4 text-amber-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">{activity.action}</p>
                    <p className="text-xs text-slate-500">{activity.user}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">{activity.time}</p>
                    <StatusBadge
                      variant={
                        activity.status === "success"
                          ? "success"
                          : activity.status === "error"
                            ? "error"
                            : "warning"
                      }
                    >
                      {activity.status === "success"
                        ? "Completed"
                        : activity.status === "error"
                          ? "Failed"
                          : "Pending"}
                    </StatusBadge>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-slate-500" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {mockQuickActions.map((action, index) => (
                <a
                  key={index}
                  href={action.path}
                  className="block rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                >
                  {action.label}
                </a>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Platform Version
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-900">v1.0.0</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Database Status
                </p>
                <p className="mt-1 text-sm font-semibold text-green-600">Connected</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Report Engine
                </p>
                <p className="mt-1 text-sm font-semibold text-green-600">Active</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Last Backup
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-900">Today, 06:00</p>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
