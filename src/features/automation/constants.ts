export interface AutomationReport {
  id: string;
  label: string;
  workflowPath: string;
  estimatedMinutes: number;
}

export const AUTOMATION_REPORTS: AutomationReport[] = [
  {
    id: "zone",
    label: "Zone Wise Report",
    workflowPath: "/workflows/merging",
    estimatedMinutes: 2,
  },
  {
    id: "division",
    label: "Division Report",
    workflowPath: "/workflows/division",
    estimatedMinutes: 2,
  },
  {
    id: "train",
    label: "Top 20 Trains",
    workflowPath: "/workflows/train-no",
    estimatedMinutes: 2,
  },
  {
    id: "cause",
    label: "Cause Wise Analysis",
    workflowPath: "/workflows/types",
    estimatedMinutes: 2,
  },
  {
    id: "scr-train",
    label: "SCR Train Report",
    workflowPath: "/workflows/scr-train",
    estimatedMinutes: 2,
  },
  {
    id: "scr-station",
    label: "SCR Station Report",
    workflowPath: "/workflows/scr-station",
    estimatedMinutes: 2,
  },
];

export const LOGIN_STEP = {
  id: "login",
  label: "Connecting to RailMadad",
} as const;

export const ESTIMATED_LOGIN_MINUTES = 1;

export function getEstimatedMinutes(reportIds: string[]): number {
  const reportMinutes = AUTOMATION_REPORTS.filter((r) => reportIds.includes(r.id)).reduce(
    (sum, r) => sum + r.estimatedMinutes,
    0,
  );
  return ESTIMATED_LOGIN_MINUTES + reportMinutes;
}

export function formatEstimatedTime(minutes: number): string {
  if (minutes < 60) {
    return `~${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `~${hours}h ${mins}m` : `~${hours}h`;
}
