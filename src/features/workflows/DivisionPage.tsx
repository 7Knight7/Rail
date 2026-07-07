import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";
import { COMMON_ADVANCED_FIELDS, EXPORT_FORMAT_FIELD } from "@/features/workflows/reportConfigFields";

const settingsFields = [
  {
    id: "reportDate",
    label: "Report Date",
    type: "date" as const,
    value: new Date().toISOString().split("T")[0],
  },
  {
    id: "topCount",
    label: "Top Count",
    type: "number" as const,
    value: 25,
    placeholder: "25",
  },
  {
    id: "sortBy",
    label: "Sort By",
    type: "select" as const,
    value: "count",
    options: [
      { value: "count", label: "Count (Descending)" },
      { value: "division", label: "Division Name" },
      { value: "percentage", label: "Percentage" },
    ],
  },
  EXPORT_FORMAT_FIELD,
];

const previewColumns = [
  { key: "rank", header: "Rank", width: "60px" },
  { key: "division", header: "Division" },
  { key: "count", header: "Count" },
  { key: "percentage", header: "Percentage" },
  { key: "change", header: "Change" },
];

const mockPreviewData = [
  { rank: 1, division: "Secunderabad", count: 1250, percentage: "18.5%", change: "+2.3%" },
  { rank: 2, division: "Hyderabad", count: 1180, percentage: "17.4%", change: "+1.8%" },
  { rank: 3, division: "Vijayawada", count: 1050, percentage: "15.5%", change: "-0.5%" },
];

export function DivisionPage() {
  return (
    <WorkflowPageLayout
      title="Division (Bottom 25)"
      description="Configure and generate the division-wise bottom 25 report"
      settingsFields={settingsFields}
      advancedFields={COMMON_ADVANCED_FIELDS}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
