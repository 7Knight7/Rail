import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";
import { COMMON_ADVANCED_FIELDS, EXPORT_FORMAT_FIELD } from "@/features/workflows/reportConfigFields";

const settingsFields = [
  { id: "reportDate", label: "Report Date", type: "date" as const, value: new Date().toISOString().split("T")[0] },
  {
    id: "zone",
    label: "Zone",
    type: "select" as const,
    value: "scr",
    options: [{ value: "scr", label: "South Central Railway" }],
  },
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

export function SCRTrainPage() {
  return (
    <WorkflowPageLayout
      reportId="scr-train"
      title="SCR Train Report"
      description="Configure and generate the SCR train complaints report"
      settingsFields={settingsFields}
      advancedFields={COMMON_ADVANCED_FIELDS}
    />
  );
}
