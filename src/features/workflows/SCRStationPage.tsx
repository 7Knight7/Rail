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
    id: "stationCategory",
    label: "Station Category",
    type: "select" as const,
    value: "all",
    options: [
      { value: "all", label: "All Categories" },
      { value: "a1", label: "A1 Category" },
      { value: "a", label: "A Category" },
      { value: "b", label: "B Category" },
      { value: "c", label: "C Category" },
    ],
  },
  {
    id: "reportType",
    label: "Report Type",
    type: "select" as const,
    value: "traffic",
    options: [
      { value: "traffic", label: "Traffic Analysis" },
      { value: "revenue", label: "Revenue Report" },
      { value: "facilities", label: "Facilities Report" },
    ],
  },
];

const previewColumns = [
  { key: "sno", header: "S.No", width: "60px" },
  { key: "stationCode", header: "Code" },
  { key: "stationName", header: "Station Name" },
  { key: "division", header: "Division" },
  { key: "footfall", header: "Daily Footfall" },
];

const mockPreviewData = [
  { sno: 1, stationCode: "SC", stationName: "Secunderabad Junction", division: "Secunderabad", footfall: "125,000" },
  { sno: 2, stationCode: "HYB", stationName: "Hyderabad Deccan", division: "Hyderabad", footfall: "85,000" },
  { sno: 3, stationCode: "BZA", stationName: "Vijayawada Junction", division: "Vijayawada", footfall: "95,000" },
  { sno: 4, stationCode: "GTL", stationName: "Guntakal Junction", division: "Guntakal", footfall: "45,000" },
  { sno: 5, stationCode: "GNT", stationName: "Guntur Junction", division: "Guntur", footfall: "38,000" },
];

export function SCRStationPage() {
  return (
    <WorkflowPageLayout
      title="SCR Station"
      description="Generate South Central Railway station analysis report"
      settingsFields={settingsFields}
      previewColumns={previewColumns}
      mockPreviewData={mockPreviewData}
    />
  );
}
