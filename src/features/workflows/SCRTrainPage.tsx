import { WorkflowPageLayout } from "@/components/workflow/WorkflowPageLayout";

const settingsFields = [
  {
    id: "reportDate",
    label: "Report Date",
    type: "date" as const,
    value: new Date().toISOString().split("T")[0],
  },
  {
    id: "zone",
    label: "Zone",
    type: "select" as const,
    value: "scr",
    options: [
      { value: "scr", label: "South Central Railway" },
      { value: "all", label: "All Zones" },
    ],
  },
  {
    id: "trainCategory",
    label: "Train Category",
    type: "select" as const,
    value: "all",
    options: [
      { value: "all", label: "All Categories" },
      { value: "longDistance", label: "Long Distance" },
      { value: "suburban", label: "Suburban" },
      { value: "intercity", label: "Inter-City" },
    ],
  },
  {
    id: "analysisType",
    label: "Analysis Type",
    type: "select" as const,
    value: "performance",
    options: [
      { value: "performance", label: "Performance Analysis" },
      { value: "punctuality", label: "Punctuality Report" },
      { value: "utilization", label: "Utilization Report" },
    ],
  },
];

const previewColumns = [
  { key: "sno", header: "S.No", width: "60px" },
  { key: "trainNo", header: "Train No" },
  { key: "trainName", header: "Train Name" },
  { key: "route", header: "Route" },
  { key: "punctuality", header: "Punctuality" },
];

const mockPreviewData = [
  { sno: 1, trainNo: "12759", trainName: "Charminar Express", route: "HYB-MAS", punctuality: "92%" },
  { sno: 2, trainNo: "12760", trainName: "Charminar Express", route: "MAS-HYB", punctuality: "89%" },
  { sno: 3, trainNo: "12785", trainName: "Falaknuma Express", route: "SC-MAS", punctuality: "94%" },
  { sno: 4, trainNo: "12786", trainName: "Falaknuma Express", route: "MAS-SC", punctuality: "91%" },
  { sno: 5, trainNo: "12713", trainName: "Satavahana Express", route: "SC-KCG", punctuality: "96%" },
];

export function SCRTrainPage() {
  return (
    <WorkflowPageLayout
      title="SCR Train"
      description="Generate South Central Railway train analysis report"
      settingsFields={settingsFields}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
