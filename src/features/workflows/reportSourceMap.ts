import type { ReportId } from "@/features/report-config/types";
import type { ReportSourceId } from "@/types/workflow";

export const SOURCE_TO_REPORT_ID: Record<ReportSourceId, ReportId> = {
  division: "division",
  train: "train-no",
  types: "types",
  "scr-train": "scr-train",
  "scr-station": "scr-station",
};

export const REPORT_ID_TO_SOURCE: Partial<Record<ReportId, ReportSourceId>> = {
  division: "division",
  "train-no": "train",
  types: "types",
  "scr-train": "scr-train",
  "scr-station": "scr-station",
  merging: "types",
};

export const SUMMARY_REPORT_OPTIONS: { id: ReportSourceId; label: string; reportId: ReportId }[] = [
  { id: "division", label: "Division Report", reportId: "division" },
  { id: "train", label: "Train Report", reportId: "train-no" },
  { id: "types", label: "Type Report", reportId: "types" },
  { id: "scr-train", label: "SCR Train", reportId: "scr-train" },
  { id: "scr-station", label: "SCR Station Report", reportId: "scr-station" },
];
