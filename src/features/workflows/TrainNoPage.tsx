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
    value: 20,
    placeholder: "20",
  },
  {
    id: "trainType",
    label: "Train Type",
    type: "select" as const,
    value: "all",
    options: [
      { value: "all", label: "All Types" },
      { value: "express", label: "Express" },
      { value: "superfast", label: "Superfast" },
      { value: "passenger", label: "Passenger" },
      { value: "mail", label: "Mail" },
    ],
  },
  {
    id: "reportType",
    label: "Report Type",
    type: "select" as const,
    value: "delay",
    options: [
      { value: "delay", label: "Delay Analysis" },
      { value: "punctuality", label: "Punctuality" },
      { value: "frequency", label: "Frequency" },
    ],
  },
];

const previewColumns = [
  { key: "rank", header: "Rank", width: "60px" },
  { key: "trainNo", header: "Train No" },
  { key: "trainName", header: "Train Name" },
  { key: "avgDelay", header: "Avg Delay" },
  { key: "instances", header: "Instances" },
];

const mockPreviewData = [
  { rank: 1, trainNo: "12345", trainName: "Rajdhani Express", avgDelay: "45 min", instances: 28 },
  { rank: 2, trainNo: "12346", trainName: "Shatabdi Express", avgDelay: "38 min", instances: 24 },
  { rank: 3, trainNo: "12347", trainName: "Duronto Express", avgDelay: "35 min", instances: 22 },
  { rank: 4, trainNo: "12348", trainName: "Garib Rath", avgDelay: "32 min", instances: 20 },
  { rank: 5, trainNo: "12349", trainName: "Jan Shatabdi", avgDelay: "28 min", instances: 18 },
];

export function TrainNoPage() {
  return (
    <WorkflowPageLayout
      title="Train No (Top 20)"
      description="Generate top 20 train number analysis report"
      settingsFields={settingsFields}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
