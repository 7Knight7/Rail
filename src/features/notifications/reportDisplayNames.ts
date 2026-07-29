const REPORT_DISPLAY_NAMES: Record<string, string> = {
  report1: "Zone Wise Complaints",
  division: "Division Wise Report",
  "train-no": "Top 20 Trains",
  types: "Cause Wise Analysis",
  "scr-train": "SCR Train Report",
  "scr-station": "SCR Station Report",
  "comprehensive-10-13": "Report 10-13 (Comprehensive Reports)",
};

export function getReportDisplayName(slug: string | null | undefined): string {
  if (!slug) return "Report";
  return REPORT_DISPLAY_NAMES[slug] ?? slug;
}
