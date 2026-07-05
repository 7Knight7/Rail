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
    value: 10,
    placeholder: "10",
  },
  {
    id: "category",
    label: "Category",
    type: "select" as const,
    value: "all",
    options: [
      { value: "all", label: "All Categories" },
      { value: "complaints", label: "Complaints" },
      { value: "maintenance", label: "Maintenance" },
      { value: "operations", label: "Operations" },
      { value: "safety", label: "Safety" },
    ],
  },
  {
    id: "groupBy",
    label: "Group By",
    type: "select" as const,
    value: "type",
    options: [
      { value: "type", label: "Issue Type" },
      { value: "severity", label: "Severity" },
      { value: "department", label: "Department" },
    ],
  },
];

const previewColumns = [
  { key: "rank", header: "Rank", width: "60px" },
  { key: "type", header: "Type" },
  { key: "count", header: "Count" },
  { key: "percentage", header: "Percentage" },
  { key: "trend", header: "Trend" },
];

const mockPreviewData = [
  { rank: 1, type: "Signal Failure", count: 156, percentage: "22.4%", trend: "+5.2%" },
  { rank: 2, type: "Track Issues", count: 134, percentage: "19.2%", trend: "+2.1%" },
  { rank: 3, type: "Power Supply", count: 98, percentage: "14.1%", trend: "-1.5%" },
  { rank: 4, type: "Communication", count: 87, percentage: "12.5%", trend: "+0.8%" },
  { rank: 5, type: "Weather Related", count: 76, percentage: "10.9%", trend: "+3.4%" },
];

export function TypesPage() {
  return (
    <WorkflowPageLayout
      title="Types (Top 10)"
      description="Generate top 10 types analysis report"
      settingsFields={settingsFields}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
