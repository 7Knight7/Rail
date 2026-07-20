import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";
import { COMMON_ADVANCED_FIELDS, EXPORT_FORMAT_FIELD } from "@/features/workflows/reportConfigFields";

const settingsFields = [
  { id: "reportDate", label: "Report Date", type: "date" as const, value: new Date().toISOString().split("T")[0] },
  {
    id: "division",
    label: "Division",
    type: "select" as const,
    value: "all",
    options: [
      { value: "all", label: "All Divisions" },
      { value: "secunderabad", label: "Secunderabad" },
      { value: "hyderabad", label: "Hyderabad" },
    ],
  },
  {
    id: "sortBy",
    label: "Sort By",
    type: "select" as const,
    value: "count",
    options: [
      { value: "count", label: "Complaint Count" },
      { value: "station", label: "Station Name" },
    ],
  },
  EXPORT_FORMAT_FIELD,
];

export function SCRStationPage() {
  return (
    <WorkflowPageLayout
      reportId="scr-station"
      title="SCR Station Report"
      description="Configure and generate the SCR station complaints report"
      settingsFields={settingsFields}
      advancedFields={COMMON_ADVANCED_FIELDS}
    />
  );
}
