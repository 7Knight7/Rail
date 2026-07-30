import { useState, useCallback, useMemo } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Spinner } from "@/components/ui/Spinner";
import { ChevronDown, ChevronUp, Download, FileText, RefreshCw } from "lucide-react";
import {
  defaultReportDateFrom,
  defaultReportDateTo,
  validateReportDateRange,
} from "@/utils/reportDateRange";
import { cn } from "@/utils/cn";
import { reportsApi } from "@/api/reports";
import { getReportDisplayName } from "@/utils/reportDisplayNames";

const AVAILABLE_COLUMNS = [
  { id: "sno", label: "S.No." },
  { id: "division", label: "Division" },
  { id: "opening_balance", label: "Opening Balance" },
  { id: "received", label: "Received" },
  { id: "share_percent", label: "% Share" },
  { id: "closed", label: "Closed" },
  { id: "closing_balance", label: "Closing Balance" },
  { id: "disposal_percent", label: "% Disposal" },
  { id: "avg_disposal_time", label: "Avg. Disposal Time" },
  { id: "avg_rating", label: "Avg. Rating" },
  { id: "avg_pendency_time", label: "Avg. Pendency Time" },
];

const DEFAULT_COLUMN_IDS = AVAILABLE_COLUMNS.map((c) => c.id);

const SECTIONS = [
  {
    id: "report10_cw",
    name: "Report 10 - C&W",
    title: "C&W complaints division wise (as per comprehensive reports)",
  },
  {
    id: "report11_security",
    name: "Report 11 - Security",
    title: "Security complaints (as per comprehensive drop down)",
  },
  {
    id: "report12_punctuality",
    name: "Report 12 - Punctuality",
    title: "Punctuality complaints (as per comprehensive drop down)",
  },
  {
    id: "report13_electrical",
    name: "Report 13 - Electrical Equipment",
    title: "Electrical Equipment complaints division wise (as per comprehensive reports)",
  },
];

interface SectionColumnState {
  selectedColumns: string[];
  expanded: boolean;
}

function SectionColumnFilter({
  section,
  selectedColumns,
  expanded,
  onToggleExpand,
  onColumnsChange,
}: {
  section: (typeof SECTIONS)[0];
  selectedColumns: string[];
  expanded: boolean;
  onToggleExpand: () => void;
  onColumnsChange: (columns: string[]) => void;
}) {
  const handleToggle = (columnId: string) => {
    if (selectedColumns.includes(columnId)) {
      if (selectedColumns.length > 1) {
        onColumnsChange(selectedColumns.filter((c) => c !== columnId));
      }
    } else {
      onColumnsChange([...selectedColumns, columnId]);
    }
  };

  const handleSelectAll = () => {
    onColumnsChange(DEFAULT_COLUMN_IDS);
  };

  const handleClearAll = () => {
    onColumnsChange([DEFAULT_COLUMN_IDS[0]]);
  };

  const handleResetDefault = () => {
    onColumnsChange(DEFAULT_COLUMN_IDS);
  };

  return (
    <Card className="border border-rail-line">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-surface/50"
        onClick={onToggleExpand}
      >
        <div>
          <h3 className="font-medium text-rail-ink">{section.name}</h3>
          <p className="text-xs text-rail-muted">{selectedColumns.length} columns selected</p>
        </div>
        {expanded ? (
          <ChevronUp size={18} className="text-rail-muted" />
        ) : (
          <ChevronDown size={18} className="text-rail-muted" />
        )}
      </button>
      {expanded && (
        <CardBody className="border-t border-rail-line pt-4">
          <div className="mb-3 flex gap-2">
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              Select All
            </Button>
            <Button variant="outline" size="sm" onClick={handleClearAll}>
              Clear All
            </Button>
            <Button variant="outline" size="sm" onClick={handleResetDefault}>
              Reset Default
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {AVAILABLE_COLUMNS.map((col) => (
              <label
                key={col.id}
                className="flex cursor-pointer items-center gap-2 rounded-lg p-2 hover:bg-surface"
              >
                <input
                  type="checkbox"
                  checked={selectedColumns.includes(col.id)}
                  onChange={() => handleToggle(col.id)}
                  className="h-4 w-4 rounded border-rail-line text-primary focus:ring-primary"
                />
                <span className="text-sm text-rail-ink">{col.label}</span>
              </label>
            ))}
          </div>
        </CardBody>
      )}
    </Card>
  );
}

export function ComprehensivePage() {
  const [dateFrom, setDateFrom] = useState(defaultReportDateFrom);
  const [dateTo, setDateTo] = useState(defaultReportDateTo);
  const [sectionStates, setSectionStates] = useState<Record<string, SectionColumnState>>(() =>
    Object.fromEntries(
      SECTIONS.map((s) => [
        s.id,
        { selectedColumns: DEFAULT_COLUMN_IDS, expanded: false },
      ]),
    ),
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<{
    success: boolean;
    message?: string;
    pdfUrl?: string;
    excelUrl?: string;
  } | null>(null);

  const dateRangeError = validateReportDateRange(dateFrom, dateTo);
  const isDateRangeValid = dateRangeError === null;

  const handleToggleExpand = useCallback((sectionId: string) => {
    setSectionStates((prev) => ({
      ...prev,
      [sectionId]: {
        ...prev[sectionId],
        expanded: !prev[sectionId].expanded,
      },
    }));
  }, []);

  const handleColumnsChange = useCallback((sectionId: string, columns: string[]) => {
    setSectionStates((prev) => ({
      ...prev,
      [sectionId]: {
        ...prev[sectionId],
        selectedColumns: columns,
      },
    }));
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!isDateRangeValid) return;

    setIsGenerating(true);
    setGenerationResult(null);

    try {
      const allSelectedColumns = DEFAULT_COLUMN_IDS;
      const columnSelection = {
        sections: Object.fromEntries(
          Object.entries(sectionStates).map(([sectionId, state]) => [
            sectionId,
            { selected_column_ids: state.selectedColumns },
          ]),
        ),
      };

      const result = await reportsApi.generate("comprehensive-10-13", {
        date_from: dateFrom,
        date_to: dateTo,
        selected_column_ids: allSelectedColumns,
        column_order: allSelectedColumns,
        export_format: "xlsx",
        requested_formats: ["xlsx", "pdf"],
        configuration_source: "manual_snapshot",
        config_overrides: {
          column_selection: columnSelection,
        },
      });

      if (result.run_id) {
        let attempts = 0;
        const maxAttempts = 60;
        const pollInterval = 3000;

        const pollStatus = async () => {
          const status = await reportsApi.getRunStatus(result.run_id, "comprehensive-10-13");
          if (status.status === "Completed") {
            setGenerationResult({
              success: true,
              message: "Report generated successfully",
              pdfUrl: status.pdf_preview_url ?? undefined,
              excelUrl: status.excel_download_url ?? undefined,
            });
            setIsGenerating(false);
          } else if (status.status === "Failed") {
            setGenerationResult({
              success: false,
              message: status.error ?? "Failed to generate report",
            });
            setIsGenerating(false);
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(pollStatus, pollInterval);
          } else {
            setGenerationResult({
              success: false,
              message: "Report generation timed out",
            });
            setIsGenerating(false);
          }
        };

        setTimeout(pollStatus, pollInterval);
      }
    } catch (error) {
      setGenerationResult({
        success: false,
        message: error instanceof Error ? error.message : "Failed to generate report",
      });
      setIsGenerating(false);
    }
  }, [dateFrom, dateTo, sectionStates, isDateRangeValid]);

  const previewData = useMemo(() => {
    return SECTIONS.map((section) => {
      const state = sectionStates[section.id];
      const columns = AVAILABLE_COLUMNS.filter((c) =>
        state.selectedColumns.includes(c.id),
      );
      return {
        section,
        columns,
        rows: [],
      };
    });
  }, [sectionStates]);

  return (
    <article className="mx-auto max-w-4xl">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold leading-snug tracking-tight text-slate-900">
          {getReportDisplayName("comprehensive-10-13")}
        </h1>
        <p className="mt-2 text-base leading-relaxed text-slate-600">
          Configure and generate comprehensive reports for C&W, Security, Punctuality, and
          Electrical Equipment complaints. Each section can have independent column selections.
        </p>
      </header>

      <div className="space-y-6">
        {generationResult && (
          <Alert
            variant={generationResult.success ? "success" : "error"}
            title={generationResult.success ? "Report Generated" : "Generation Failed"}
          >
            {generationResult.message}
          </Alert>
        )}

        <Card>
          <CardHeader>
            <h2 className="text-lg font-medium text-rail-ink">Date Range</h2>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="dateFrom" className="text-sm font-medium text-rail-muted">
                  From Date
                </label>
                <input
                  type="date"
                  id="dateFrom"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="rounded-lg border border-rail-line px-3 py-2 text-sm"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor="dateTo" className="text-sm font-medium text-rail-muted">
                  To Date
                </label>
                <input
                  type="date"
                  id="dateTo"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="rounded-lg border border-rail-line px-3 py-2 text-sm"
                />
              </div>
            </div>
            {dateRangeError && (
              <p className="mt-2 text-sm text-red-600">{dateRangeError}</p>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-medium text-rail-ink">Section Column Filters</h2>
            <p className="text-sm text-rail-muted">
              Configure which columns to include for each section. Changes apply immediately to preview.
            </p>
          </CardHeader>
          <CardBody className="space-y-3">
            {SECTIONS.map((section) => (
              <SectionColumnFilter
                key={section.id}
                section={section}
                selectedColumns={sectionStates[section.id].selectedColumns}
                expanded={sectionStates[section.id].expanded}
                onToggleExpand={() => handleToggleExpand(section.id)}
                onColumnsChange={(cols) => handleColumnsChange(section.id, cols)}
              />
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-medium text-rail-ink">Preview</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-6">
              {previewData.map(({ section, columns }) => (
                <div key={section.id} className="rounded-lg border border-rail-line p-4">
                  <h3 className="mb-2 font-medium text-rail-ink">{section.title}</h3>
                  <p className="text-sm text-rail-muted">
                    Columns: {columns.map((c) => c.label).join(", ")}
                  </p>
                  <p className="mt-1 text-xs text-rail-muted">
                    Data will be populated after generation
                  </p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <div className="flex items-center justify-between rounded-xl border border-rail-line bg-white p-4">
          <div className="text-sm text-rail-muted">
            {isGenerating ? "Generating report..." : "Ready to generate"}
          </div>
          <div className="flex gap-3">
            {generationResult?.success && (
              <>
                {generationResult.pdfUrl && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(generationResult.pdfUrl, "_blank")}
                  >
                    <FileText size={16} className="mr-2" />
                    Preview PDF
                  </Button>
                )}
                {generationResult.excelUrl && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(generationResult.excelUrl, "_blank")}
                  >
                    <Download size={16} className="mr-2" />
                    Download Excel
                  </Button>
                )}
              </>
            )}
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !isDateRangeValid}
            >
              {isGenerating ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <RefreshCw size={16} className="mr-2" />
                  Generate Report
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </article>
  );
}
