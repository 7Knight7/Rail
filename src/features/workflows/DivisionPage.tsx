import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";

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
  {
    id: "includeSubDivisions",
    label: "Include Sub-Divisions",
    type: "select" as const,
    value: "yes",
    options: [
      { value: "yes", label: "Yes" },
      { value: "no", label: "No" },
    ],
  },
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
  { rank: 4, division: "Guntakal", count: 890, percentage: "13.2%", change: "+0.9%" },
  { rank: 5, division: "Guntur", count: 780, percentage: "11.5%", change: "+1.2%" },
  { rank: 6, division: "Nanded", count: 650, percentage: "9.6%", change: "-0.3%" },
];

export function DivisionPage() {
  return (
    <WorkflowPageLayout
      title="Division (Top 25)"
      description="Generate top 25 division-wise analysis report"
      settingsFields={settingsFields}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
