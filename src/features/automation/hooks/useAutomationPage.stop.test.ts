import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/client", () => ({
  apiRequest: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(
      message: string,
      public status: number,
    ) {
      super(message);
      this.name = "ApiError";
    }
  },
}));

import { apiRequest } from "@/api/client";
import { automationApi } from "@/api/automation";
import {
  isTerminalRunStatus,
  shouldResumeRun,
} from "@/features/automation/hooks/useAutomationPage";

const mockApiRequest = vi.mocked(apiRequest);

describe("stop generation helpers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("stop API is called with run_id", async () => {
    mockApiRequest.mockResolvedValue({
      success: true,
      status: "stopped",
      message: "Automation stopped",
      run_id: "abc",
    });

    const res = await automationApi.stop("abc");

    expect(mockApiRequest).toHaveBeenCalledWith("/automation/runs/abc/stop", {
      method: "POST",
    });
    expect(res.success).toBe(true);
    expect(res.status).toBe("stopped");
  });

  it("never auto-resumes progress after login or refresh", () => {
    expect(shouldResumeRun("running")).toBe(false);
    expect(shouldResumeRun("paused")).toBe(false);
    expect(shouldResumeRun("pending")).toBe(false);
    expect(shouldResumeRun("stopped")).toBe(false);
    expect(shouldResumeRun("cancelled")).toBe(false);
    expect(shouldResumeRun("completed")).toBe(false);
    expect(shouldResumeRun("failed")).toBe(false);
  });

  it("terminal statuses clear active progress polling", () => {
    expect(isTerminalRunStatus("stopped")).toBe(true);
    expect(isTerminalRunStatus("running")).toBe(false);
  });

  it("pause and resume API are called with run_id", async () => {
    mockApiRequest.mockResolvedValue({
      success: true,
      status: "pause_requested",
      message: "Pause requested",
      run_id: "abc",
    });

    await automationApi.pause("abc");
    expect(mockApiRequest).toHaveBeenCalledWith("/automation/runs/abc/pause", {
      method: "POST",
    });

    mockApiRequest.mockResolvedValue({
      success: true,
      status: "running",
      message: "Automation resumed",
      run_id: "abc",
    });
    await automationApi.resume("abc");
    expect(mockApiRequest).toHaveBeenCalledWith("/automation/runs/abc/resume", {
      method: "POST",
    });
  });

  it("engine stop fallback without run_id still uses /automation/stop", async () => {
    mockApiRequest.mockResolvedValue({
      success: true,
      status: "stopped",
      message: "Automation stopped",
    });

    await automationApi.stop();

    expect(mockApiRequest).toHaveBeenCalledWith("/automation/stop", {
      method: "POST",
    });
  });
});
