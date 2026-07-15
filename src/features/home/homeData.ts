import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Building2,
  Clock,
  FileCheck,
  FolderOpen,
  Layers,
  MapPin,
  ScrollText,
  SlidersHorizontal,
  Timer,
  Train,
} from "lucide-react";

export interface ScheduledReport {
  /** Backend report catalog slug — cards are matched by slug, never position. */
  id: string;
  name: string;
  icon: LucideIcon;
  duration: string;
  status: "Ready" | "Scheduled" | "Generated";
  path: string;
}

export const SCHEDULED_REPORTS: ScheduledReport[] = [
  {
    id: "report1",
    name: "Zone Wise Complaints",
    icon: MapPin,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/merging",
  },
  {
    id: "division",
    name: "Division Bottom 25",
    icon: Building2,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/division",
  },
  {
    id: "train-no",
    name: "Top 20 Trains",
    icon: Train,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/train-no",
  },
  {
    id: "types",
    name: "Cause Wise Analysis",
    icon: BarChart3,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/types",
  },
  {
    id: "scr-train",
    name: "SCR Train Report",
    icon: Train,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/scr-train",
  },
  {
    id: "scr-station",
    name: "SCR Station Report",
    icon: Building2,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/scr-station",
  },
];

/** Icons for the live status metric cards (values come from /dashboard/summary). */
export const METRIC_ICONS = {
  lastGenerated: Clock,
  reportsAvailable: FileCheck,
  expectedTime: Timer,
  currentStatus: Layers,
} as const;

export const GENERATION_PIPELINE = [
  { step: 1, label: "Collect Report Data" },
  { step: 2, label: "Generate Reports" },
  { step: 3, label: "Update Dashboard" },
  { step: 4, label: "Generate PDFs" },
  { step: 5, label: "Ready for Download" },
];

export const QUICK_ACTIONS = [
  {
    label: "View Dashboard",
    description: "Analytics and complaint insights",
    icon: BarChart3,
    path: "/dashboard",
    permission: null,
  },
  {
    label: "Generated Reports",
    description: "Browse and download files",
    icon: FolderOpen,
    path: "/reports",
    permission: "reports" as const,
  },
  {
    label: "Report Configuration",
    description: "Filters and export settings",
    icon: SlidersHorizontal,
    path: "/workflows/merging",
    permission: null,
  },
  {
    label: "Activity Log",
    description: "Generation history and events",
    icon: ScrollText,
    path: "/logs",
    permission: "logs" as const,
  },
];
