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
  id: string;
  name: string;
  icon: LucideIcon;
  duration: string;
  status: "Ready" | "Scheduled" | "Generated";
  path: string;
}

export const SCHEDULED_REPORTS: ScheduledReport[] = [
  {
    id: "zone",
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
    id: "train",
    name: "Top 20 Trains",
    icon: Train,
    duration: "~2 min",
    status: "Ready",
    path: "/workflows/train-no",
  },
  {
    id: "cause",
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

export const STATUS_METRICS = [
  {
    icon: Clock,
    title: "Last Generated",
    value: "Yesterday 5:42 PM",
    description: "All 7 reports completed successfully",
  },
  {
    icon: FileCheck,
    title: "Reports Available",
    value: "7 Reports",
    description: "Ready to preview and download",
  },
  {
    icon: Timer,
    title: "Expected Time",
    value: "2–3 Minutes",
    description: "Typical daily generation duration",
  },
  {
    icon: Layers,
    title: "Current Status",
    value: "Ready",
    description: "No generation in progress",
    accent: true,
  },
];

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
