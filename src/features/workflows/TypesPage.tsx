import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";
import { COMMON_ADVANCED_FIELDS, EXPORT_FORMAT_FIELD } from "@/features/workflows/reportConfigFields";

const settingsFields = [
  { id: "reportDate", label: "Report Date", type: "date" as const, value: new Date().toISOString().split("T")[0] },
  { id: "topCount", label: "Top Count", type: "number" as const, value: 10, placeholder: "10" },
  {
    id: "sortBy",
    label: "Sort By",
    type: "select" as const,
    value: "count",
    options: [
      { value: "count", label: "Count" },
      { value: "category", label: "Category" },
    ],
  },
  EXPORT_FORMAT_FIELD,
];

const previewColumns = [
  { key: "rank", header: "Rank", width: "60px" },
  { key: "cause", header: "Cause" },
  { key: "count", header: "Count" },
  { key: "percentage", header: "Percentage" },
];

export function TypesPage() {
  return (
    <WorkflowPageLayout
      title="Cause Wise Analysis"
      description="Configure and generate the cause-wise analysis report"
      settingsFields={settingsFields}
      advancedFields={COMMON_ADVANCED_FIELDS}
      previewColumns={previewColumns}
    />
  );
}
