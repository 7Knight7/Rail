import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Download,
  Eye,
  FileSpreadsheet,
  RefreshCw,
  Archive,
} from "lucide-react";
import {
  automationApi,
  type AutomationArtifact,
  type AutomationRunDetail,
  type CdpRunSummary,
  type ReportResult,
} from "@/api/automation";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from "@/utils/cn";
import { formatDateTime12h } from "@/utils/datetime";

const LAST_RUN_KEY = "railmadad_last_run_id";

function triggerBlobDownload(blob: Blob, filename: string) {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export function GeneratedReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const runIdFromUrl = searchParams.get("run_id");
  const [runs, setRuns] = useState<CdpRunSummary[]>([]);
  const [run, setRun] = useState<AutomationRunDetail | null>(null);
  const [artifacts, setArtifacts] = useState<AutomationArtifact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const selectedRunId = runIdFromUrl || localStorage.getItem(LAST_RUN_KEY);

  const loadRuns = useCallback(async () => {
    try {
      const list = await automationApi.listCdpRuns(30);
      setRuns(list);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const loadRun = useCallback(async (runId: string) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await automationApi.getRun(runId);
      const arts = await automationApi.getRunArtifacts(runId);
      setRun(detail);
      setArtifacts(arts);
      localStorage.setItem(LAST_RUN_KEY, runId);
      setSearchParams({ run_id: runId }, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run");
      setRun(null);
      setArtifacts([]);
    } finally {
      setLoading(false);
    }
  }, [setSearchParams]);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    if (selectedRunId) {
      void loadRun(selectedRunId);
    }
  }, [selectedRunId, loadRun]);

  const artifactsBySlug = useMemo(() => {
    const map = new Map<string, { pdf?: AutomationArtifact; excel?: AutomationArtifact }>();
    for (const art of artifacts) {
      const slug = art.report_slug || art.report_name || "unknown";
      const entry = map.get(slug) ?? {};
      if (art.file_type === "pdf") entry.pdf = art;
      if (art.file_type === "excel") entry.excel = art;
      map.set(slug, entry);
    }
    return map;
  }, [artifacts]);

  const reports: ReportResult[] = run?.reports?.length
    ? run.reports
    : Array.from(artifactsBySlug.keys()).map((slug) => ({
        slug,
        status: "success" as const,
      }));

  const onDownload = async (url: string | null | undefined, filename: string, key: string) => {
    if (!url) {
      setError("File is not available yet");
      return;
    }
    setBusy(key);
    setError(null);
    try {
      const { blob, filename: serverName } = await automationApi.downloadBlob(url, filename);
      triggerBlobDownload(blob, serverName || filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setBusy(null);
    }
  };

  const onRetry = async (slug: string) => {
    setBusy(`retry-${slug}`);
    setError(null);
    try {
      const result = await automationApi.start({ report_slugs: [slug] });
      if (result.run_id) {
        await loadRun(result.run_id);
        await loadRuns();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Run Results"
        description="Review and download Excel/PDF artifacts from automation runs."
      />

      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <Card className="h-fit border-rail-line">
          <CardHeader>
            <CardTitle className="text-sm">Previous runs</CardTitle>
            <CardDescription>Select a run to review</CardDescription>
          </CardHeader>
          <CardBody className="space-y-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => void loadRuns()}
            >
              <RefreshCw className="mr-1 h-3.5 w-3.5" />
              Refresh
            </Button>
            {runs.length === 0 ? (
              <p className="text-xs text-slate-500">No CDP runs yet.</p>
            ) : (
              <ul className="max-h-[28rem] space-y-1 overflow-auto">
                {runs.map((item) => (
                  <li key={item.run_id}>
                    <button
                      type="button"
                      className={cn(
                        "w-full rounded-md px-2 py-2 text-left text-xs",
                        selectedRunId === item.run_id
                          ? "bg-slate-900 text-white"
                          : "hover:bg-slate-100 text-slate-700",
                      )}
                      onClick={() => void loadRun(item.run_id)}
                    >
                      <div className="font-medium">{item.status}</div>
                      <div className="opacity-80">
                        {item.started_at
                          ? formatDateTime12h(item.started_at)
                          : item.run_id.slice(0, 8)}
                      </div>
                      <div className="opacity-70">
                        ok {item.success_count} / fail {item.failure_count}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>

        <div className="space-y-4">
          {error ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          {loading ? <p className="text-sm text-slate-500">Loading run…</p> : null}

          {!loading && !run ? (
            <Card>
              <CardBody className="space-y-3 py-10 text-center">
                <p className="text-sm text-slate-600">
                  No run selected. Start automation, then return here to review outputs.
                </p>
                <Button asChild>
                  <Link to="/automation">Go to Automation</Link>
                </Button>
              </CardBody>
            </Card>
          ) : null}

          {run ? (
            <>
              <Card className="border-rail-line">
                <CardHeader className="flex flex-row items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">Run {run.run_id.slice(0, 8)}…</CardTitle>
                    <CardDescription>
                      Status: {run.status}
                      {run.total_duration_seconds != null
                        ? ` · ${Math.round(run.total_duration_seconds / 60)}m ${Math.round(
                            run.total_duration_seconds % 60,
                          )}s`
                        : ""}
                    </CardDescription>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={!run.download_all_url || busy === "zip"}
                    onClick={() =>
                      void onDownload(
                        run.download_all_url || automationApi.downloadAllUrl(run.run_id),
                        `Rail_Madad_Reports.zip`,
                        "zip",
                      )
                    }
                  >
                    <Archive className="mr-1 h-3.5 w-3.5" />
                    Download All
                  </Button>
                </CardHeader>
              </Card>

              <div className="grid gap-4 md:grid-cols-2">
                {reports.map((report) => {
                  const arts = artifactsBySlug.get(report.slug) ?? {};
                  const preview =
                    arts.pdf?.preview_url ||
                    report.pdf_preview_url ||
                    (arts.pdf ? automationApi.artifactPreviewUrl(arts.pdf.id) : null);
                  const pdfDl =
                    arts.pdf?.status === "ready"
                      ? arts.pdf.download_url ||
                        (arts.pdf ? automationApi.artifactDownloadUrl(arts.pdf.id) : null)
                      : report.pdf_download_url || null;
                  const excelDl =
                    arts.excel?.download_url ||
                    report.excel_download_url ||
                    (arts.excel ? automationApi.artifactDownloadUrl(arts.excel.id) : null);
                  const hasCurrentPdfUrl = Boolean(preview || pdfDl || report.pdf_download_url);
                  const hasCurrentExcelUrl = Boolean(excelDl);
                  const pdfReady =
                    arts.pdf?.status === "ready" || Boolean(report.pdf_download_url);
                  const excelReady =
                    arts.excel?.status === "ready" || Boolean(report.excel_download_url);
                  const failed = report.status === "failed";
                  const terminalPartial = report.status === "partial_success";
                  // Terminal success must never show deferred/stale pending error text.
                  const displayError =
                    report.status === "success" ? null : report.error || null;

                  return (
                    <Card key={report.slug} className="border-rail-line">
                      <CardHeader>
                        <CardTitle className="text-sm">{report.slug}</CardTitle>
                        <CardDescription>
                          {report.status}
                          {report.row_count != null || report.source_row_count != null
                            ? ` · ${report.row_count ?? report.source_row_count} rows`
                            : ""}
                          {report.duration_seconds != null
                            ? ` · ${report.duration_seconds.toFixed(1)}s`
                            : ""}
                        </CardDescription>
                      </CardHeader>
                      <CardBody className="space-y-3">
                        {displayError ? (
                          <p className="text-xs text-red-600">{displayError}</p>
                        ) : null}
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            disabled={!pdfReady || !preview || !hasCurrentPdfUrl}
                            onClick={() => setPreviewUrl(preview)}
                          >
                            <Eye className="mr-1 h-3.5 w-3.5" />
                            Preview PDF
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            disabled={!pdfReady || !pdfDl || !hasCurrentPdfUrl || busy === `pdf-${report.slug}`}
                            onClick={() =>
                              void onDownload(
                                pdfDl || automationApi.pdfDownloadUrl(report.slug),
                                `${report.slug}.pdf`,
                                `pdf-${report.slug}`,
                              )
                            }
                          >
                            <Download className="mr-1 h-3.5 w-3.5" />
                            Download PDF
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            disabled={!excelReady || !excelDl || !hasCurrentExcelUrl || busy === `xlsx-${report.slug}`}
                            onClick={() =>
                              void onDownload(
                                excelDl,
                                `${report.slug}.xlsx`,
                                `xlsx-${report.slug}`,
                              )
                            }
                          >
                            <FileSpreadsheet className="mr-1 h-3.5 w-3.5" />
                            Download Excel
                          </Button>
                          {failed || terminalPartial ? (
                            <Button
                              type="button"
                              size="sm"
                              disabled={busy === `retry-${report.slug}`}
                              onClick={() => void onRetry(report.slug)}
                            >
                              Retry
                            </Button>
                          ) : null}
                        </div>
                      </CardBody>
                    </Card>
                  );
                })}
              </div>
            </>
          ) : null}
        </div>
      </div>

      {previewUrl ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-900">PDF Review</h2>
              <Button type="button" variant="secondary" size="sm" onClick={() => setPreviewUrl(null)}>
                Close
              </Button>
            </div>
            <iframe title="PDF preview" src={previewUrl} className="h-full w-full flex-1" />
          </div>
        </div>
      ) : null}
    </div>
  );
}
