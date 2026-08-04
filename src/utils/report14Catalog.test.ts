import { describe, expect, it } from "vitest";
import { getReportDisplayName, REPORT_SLUG_ORDER, WORKFLOW_PATHS } from "@/utils/reportDisplayNames";
import { SCHEDULED_REPORTS } from "@/features/home/homeData";
import { AUTOMATION_REPORTS } from "@/features/automation/constants";

describe("Report 14 catalog registration", () => {
  it("is 9th after comprehensive-10-13 in slug order", () => {
    expect(REPORT_SLUG_ORDER).toHaveLength(9);
    expect(REPORT_SLUG_ORDER[7]).toBe("comprehensive-10-13");
    expect(REPORT_SLUG_ORDER[8]).toBe("report14");
  });

  it("has display name and workflow path", () => {
    expect(getReportDisplayName("report14")).toBe("Report 14: Watering Complaints");
    const path = WORKFLOW_PATHS.find((w) => w.slug === "report14");
    expect(path?.path).toBe("/workflows/report14");
  });

  it("is on home scheduled reports as 9th card", () => {
    expect(SCHEDULED_REPORTS).toHaveLength(9);
    expect(SCHEDULED_REPORTS[8].id).toBe("report14");
    expect(SCHEDULED_REPORTS[8].path).toBe("/workflows/report14");
  });

  it("is on automation reports as 9th step", () => {
    expect(AUTOMATION_REPORTS).toHaveLength(9);
    expect(AUTOMATION_REPORTS[8].id).toBe("report14");
    expect(AUTOMATION_REPORTS[8].workflowPath).toBe("/workflows/report14");
  });
});
