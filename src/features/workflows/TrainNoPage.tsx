import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";
import { COMMON_ADVANCED_FIELDS, EXPORT_FORMAT_FIELD } from "@/features/workflows/reportConfigFields";

const settingsFields = [
  { id: "reportDate", label: "Report Date", type: "date" as const, value: new Date().toISOString().split("T")[0] },
  { id: "topCount", label: "Top Count", type: "number" as const, value: 20, placeholder: "20" },
  {
    id: "sortBy",
    label: "Sort By",
    type: "select" as const,
    value: "count",
    options: [
      { value: "count", label: "Complaint Count" },
      { value: "train", label: "Train Number" },
    ],
  },
  EXPORT_FORMAT_FIELD,
];

const previewColumns = [
  { key: "rank", header: "Rank", width: "60px" },
  { key: "trainNo", header: "Train No" },
  { key: "count", header: "Complaints" },
  { key: "route", header: "Route" },
];

export function TrainNoPage() {
  return (
    <WorkflowPageLayout
      title="Top 20 Trains"
      description="Configure and generate the top 20 complaint trains report"
      settingsFields={settingsFields}
      advancedFields={COMMON_ADVANCED_FIELDS}
      previewColumns={previewColumns}
    />
  );
}
