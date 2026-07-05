import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";

const settingsFields = [
  {
    id: "reportDate",
    label: "Report Date",
    type: "date" as const,
    value: new Date().toISOString().split("T")[0],
  },
  {
    id: "division",
    label: "Division",
    type: "select" as const,
    value: "all",
    options: [
      { value: "all", label: "All Divisions" },
      { value: "secunderabad", label: "Secunderabad" },
      { value: "hyderabad", label: "Hyderabad" },
      { value: "vijayawada", label: "Vijayawada" },
      { value: "guntakal", label: "Guntakal" },
      { value: "guntur", label: "Guntur" },
      { value: "nanded", label: "Nanded" },
    ],
  },
  {
    id: "mergeType",
    label: "Merge Type",
    type: "select" as const,
    value: "standard",
    options: [
      { value: "standard", label: "Standard Merge" },
      { value: "consolidated", label: "Consolidated" },
      { value: "detailed", label: "Detailed" },
    ],
  },
  {
    id: "outputFormat",
    label: "Output Format",
    type: "select" as const,
    value: "xlsx",
    options: [
      { value: "xlsx", label: "Excel (.xlsx)" },
      { value: "csv", label: "CSV" },
      { value: "pdf", label: "PDF" },
    ],
  },
];

const previewColumns = [
  { key: "sno", header: "S.No", width: "60px" },
  { key: "trainNo", header: "Train No" },
  { key: "division", header: "Division" },
  { key: "date", header: "Date" },
  { key: "status", header: "Status" },
];

const mockPreviewData = [
  { sno: 1, trainNo: "12345", division: "Secunderabad", date: "2026-07-04", status: "Completed" },
  { sno: 2, trainNo: "12346", division: "Hyderabad", date: "2026-07-04", status: "Pending" },
  { sno: 3, trainNo: "12347", division: "Vijayawada", date: "2026-07-04", status: "Completed" },
  { sno: 4, trainNo: "12348", division: "Guntakal", date: "2026-07-04", status: "Completed" },
  { sno: 5, trainNo: "12349", division: "Guntur", date: "2026-07-04", status: "Pending" },
];

export function MergingPage() {
  return (
    <WorkflowPageLayout
      title="Merging"
      description="Merge multiple report files into a consolidated output"
      settingsFields={settingsFields}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
