import { Link } from "react-router-dom";
import { CheckCircle2, Download } from "lucide-react";
import { useCallback, useState } from "react";
import { automationApi } from "@/api/automation";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import type { AutomationCompletionSummary } from "@/features/automation/types/automation";
import { formatDuration } from "@/features/automation/utils/display";

export interface AutomationCompletionSummaryProps {
  summary: AutomationCompletionSummary;
}

export function AutomationCompletionSummaryCard({ summary }: AutomationCompletionSummaryProps) {
  const [downloading, setDownloading] = useState<string | null>(null);

  const onDownload = useCallback(async (slug: string, url: string) => {
    setDownloading(slug);
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/pdf" },
      });
      if (!response.ok) {
        throw new Error(`Download failed (${response.status})`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `${slug}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (error) {
      console.error("PDF download failed", error);
    } finally {
      setDownloading(null);
    }
  }, []);

  const downloads = summary.reportDownloads ?? [];

  return (
    <Card className="border-rail-line shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-slate-900">
          <CheckCircle2 className="h-5 w-5 text-green-600" />
          Reports ready
        </CardTitle>
        <CardDescription>Today&apos;s reports have been generated successfully.</CardDescription>
      </CardHeader>
      <CardBody className="space-y-6">
        <ul className="space-y-3 text-sm text-slate-700">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            Reports Generated ({summary.reportsGenerated})
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            Dashboard Updated
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            Reports Ready
          </li>
        </ul>

        {downloads.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-800">Download PDFs</p>
            <ul className="space-y-2">
              {downloads.map((item) => (
                <li key={item.slug} className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-slate-700">{item.datasetKey || item.slug}</span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={downloading === item.slug}
                    onClick={() =>
                      void onDownload(
                        item.slug,
                        item.pdfDownloadUrl || automationApi.pdfDownloadUrl(item.slug),
                      )
                    }
                  >
                    <Download className="mr-1 h-3.5 w-3.5" />
                    {downloading === item.slug ? "Downloading…" : "Download PDF"}
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <p className="text-xs text-slate-500">
          Completed in {formatDuration(summary.executionTimeMs)}
        </p>
        <Button asChild>
          <Link to="/dashboard">View Dashboard</Link>
        </Button>
      </CardBody>
    </Card>
  );
}
