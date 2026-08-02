import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SettingsCard } from "@/components/workflow/SettingsCard";
import { ActionBar } from "@/components/workflow/ActionBar";
import { OutputCard } from "@/components/workflow/OutputCard";
import { useComprehensiveReportGeneration, resolveComprehensiveExportFormat } from "@/components/workflow/useComprehensiveReportGeneration";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { formatFileSize, reportsApi } from "@/api/reports";
import {
  COMPREHENSIVE_EXPORT_FORMAT_FIELD,
  REPORT_DATE_RANGE_FIELDS,
} from "@/features/workflows/reportConfigFields";
import { ComprehensiveFilterSummary } from "@/features/workflows/ComprehensiveFilterSummary";
import {
  AVAILABLE_COLUMNS,
  buildDefaultSectionStates,
  COMPREHENSIVE_REPORT_ID,
  DEFAULT_COLUMN_IDS,
  SECTIONS,
  type SectionColumnState,
  validateSectionSelections,
} from "@/features/workflows/comprehensiveConstants";
import {
  defaultReportDateFrom,
  defaultReportDateTo,
  validateReportDateRange,
} from "@/utils/reportDateRange";
import {
  getReportDisplayName,
  getReportDownloadName,
} from "@/utils/reportDisplayNames";

const settingsFields = [...REPORT_DATE_RANGE_FIELDS, COMPREHENSIVE_EXPORT_FORMAT_FIELD];

function applyDefaultDateRange(
  fields: typeof settingsFields,
): Array<(typeof settingsFields)[number]> {
  return fields.map((field) => {
    if (field.id === "dateFrom") {
      return { ...field, value: defaultReportDateFrom() };
    }
    if (field.id === "dateTo") {
      return { ...field, value: defaultReportDateTo() };
    }
    return field;
  });
}

function SectionColumnFilter({
  section,
  selectedColumns,
  expanded,
  onToggleExpand,
  onColumnsChange,
  disabled,
}: {
  section: (typeof SECTIONS)[0];
  selectedColumns: string[];
  expanded: boolean;
  onToggleExpand: () => void;
  onColumnsChange: (columns: string[]) => void;
  disabled?: boolean;
}) {
  const handleToggle = (columnId: string) => {
    if (disabled) return;
    if (selectedColumns.includes(columnId)) {
      onColumnsChange(selectedColumns.filter((c) => c !== columnId));
    } else {
      onColumnsChange([...selectedColumns, columnId]);
    }
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
            <Button
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={() => onColumnsChange(DEFAULT_COLUMN_IDS)}
            >
              Select All
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={() => onColumnsChange([])}
            >
              Clear All
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={() => onColumnsChange(DEFAULT_COLUMN_IDS)}
            >
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
                  disabled={disabled}
                  aria-label={col.label}
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
  const [settings, setSettings] = useState(() => applyDefaultDateRange(settingsFields));
  const [sectionStates, setSectionStates] = useState<Record<string, SectionColumnState>>(
    buildDefaultSectionStates,
  );
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const configLoadedRef = useRef(false);

  const {
    status,
    manualStatus,
    runState,
    errorMessage,
    settingsChanged,
    handleGenerate,
    handleSaveConfiguration,
    handleDownloadExcel,
    handleDownloadPdf,
    handlePreviewPdf,
    resetGeneration,
    canDownload,
    canDownloadExcel,
    canDownloadPdf,
    canPreviewPdf,
    dualOutputMode,
  } = useComprehensiveReportGeneration({ sectionStates, settings });

  const dateFrom = String(settings.find((f) => f.id === "dateFrom")?.value ?? "");
  const dateTo = String(settings.find((f) => f.id === "dateTo")?.value ?? "");
  const dateRangeError = validateReportDateRange(dateFrom, dateTo);
  const isDateRangeValid = dateRangeError === null;
  const sectionValidationError = useMemo(
    () => validateSectionSelections(sectionStates),
    [sectionStates],
  );

  const displayTitle = getReportDisplayName(COMPREHENSIVE_REPORT_ID);
  const downloadTitle = getReportDownloadName(COMPREHENSIVE_REPORT_ID);

  useEffect(() => {
    let cancelled = false;
    void reportsApi.loadConfig(COMPREHENSIVE_REPORT_ID).then((saved) => {
      if (cancelled || !saved || configLoadedRef.current) return;
      configLoadedRef.current = true;


      if (saved.date_from || saved.date_to || saved.export_format || saved.config_overrides) {
        setSettings((prev) =>
          prev.map((field) => {
            if (field.id === "dateFrom" && saved.date_from) {
              return { ...field, value: saved.date_from };
            }
            if (field.id === "dateTo" && saved.date_to) {
              return { ...field, value: saved.date_to };
            }

            if (field.id === "exportFormat") {
              return { ...field, value: resolveComprehensiveExportFormat(saved) };
            }
            return field;
          }),
        );
      }

      const savedSections = saved.sections;
      if (savedSections && Object.keys(savedSections).length > 0) {
        setSectionStates((prev) => {
          const next = { ...prev };
          for (const section of SECTIONS) {
            const sectionPayload = savedSections[section.id];
            const selected = sectionPayload?.selected_column_ids;
            if (selected && selected.length > 0) {
              next[section.id] = {
                ...next[section.id],
                selectedColumns: selected.filter((id) => DEFAULT_COLUMN_IDS.includes(id)),
              };
            }
          }
          return next;
        });
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSettingChange = useCallback((id: string, value: string | number) => {
    setSettings((prev) =>
      prev.map((field) => (field.id === id ? { ...field, value } : field)),
    );
  }, []);

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

  const triggerBlobDownload = useCallback((blob: Blob, filename: string) => {
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
  }, []);

  const onGenerate = useCallback(() => {
    if (!isDateRangeValid) {
      alert(dateRangeError);
      return;
    }
    void handleGenerate();
  }, [dateRangeError, handleGenerate, isDateRangeValid]);

  const onSave = useCallback(async () => {
    try {
      await handleSaveConfiguration();
      setSaveMessage("Configuration saved.");
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save configuration.");
    }
  }, [handleSaveConfiguration]);

  const loadDefaults = useCallback(() => {
    setSettings(applyDefaultDateRange(settingsFields));
    setSectionStates(buildDefaultSectionStates());
  }, []);

  const handleReset = useCallback(async () => {
    const isDirty =
      settingsChanged ||
      status !== "idle" ||
      runState !== null ||
      sectionValidationError !== null;

    if (isDirty && !window.confirm("Reset all settings to saved defaults?")) {
      return;
    }

    resetGeneration();
    const saved = await reportsApi.loadConfig(COMPREHENSIVE_REPORT_ID);
    if (saved) {
      configLoadedRef.current = true;

      if (saved.date_from || saved.date_to || saved.export_format || saved.config_overrides) {
        setSettings((prev) =>
          prev.map((field) => {
            if (field.id === "dateFrom" && saved.date_from) {
              return { ...field, value: saved.date_from };
            }
            if (field.id === "dateTo" && saved.date_to) {
              return { ...field, value: saved.date_to };
            }

            if (field.id === "exportFormat") {
              return { ...field, value: resolveComprehensiveExportFormat(saved) };
            }
            return field;
          }),
        );
      }
      const savedSections = saved.sections;
      if (savedSections && Object.keys(savedSections).length > 0) {
        setSectionStates(() => {
          const next = buildDefaultSectionStates();
          for (const section of SECTIONS) {
            const sectionPayload = savedSections[section.id];
            const selected = sectionPayload?.selected_column_ids;
            if (selected && selected.length > 0) {
              next[section.id] = {
                ...next[section.id],
                selectedColumns: selected.filter((id) => DEFAULT_COLUMN_IDS.includes(id)),
              };
            }
          }
          return next;
        });
      } else {
        setSectionStates(buildDefaultSectionStates());
      }
    } else {
      loadDefaults();
    }
  }, [
    loadDefaults,
    resetGeneration,
    runState,
    sectionValidationError,
    settingsChanged,
    status,
  ]);

  const onDownloadExcel = useCallback(async () => {
    try {
      const { blob, filename } = await handleDownloadExcel();
      triggerBlobDownload(blob, filename);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Excel download failed.");
    }
  }, [handleDownloadExcel, triggerBlobDownload]);

  const onDownloadPdf = useCallback(async () => {
    try {
      const { blob, filename } = await handleDownloadPdf();
      triggerBlobDownload(blob, filename);
    } catch (err) {
      alert(err instanceof Error ? err.message : "PDF download failed.");
    }
  }, [handleDownloadPdf, triggerBlobDownload]);

  const onPreviewPdf = useCallback(() => {
    try {
      handlePreviewPdf();
    } catch (err) {
      alert(err instanceof Error ? err.message : "PDF preview failed.");
    }
  }, [handlePreviewPdf]);

  const isProcessing = status === "processing";

  return (
    <div className="space-y-8">
      <PageHeader
        title={displayTitle}
        description="C&W, Security, Punctuality and Electrical Equipment division-wise complaint reports"
        breadcrumbs={[
          { label: "Report Configuration", href: "/workflows" },
          { label: displayTitle },
        ]}
      />

      <ComprehensiveFilterSummary />

      <SettingsCard
        title="Report Settings"
        description="Configure how this grouped report should be generated"
        fields={settings}
        onChange={handleSettingChange}
        disabled={isProcessing}
      />

      {dateRangeError && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-800">
          {dateRangeError}
        </p>
      )}

      <Card className="rounded-2xl border border-rail-line shadow-card">
        <CardHeader className="border-b border-rail-line">
          <CardTitle>Section Column Filters</CardTitle>
          <CardDescription>
            Configure which columns to include for each section. Selections are independent per
            section.
          </CardDescription>
        </CardHeader>
        <CardBody className="space-y-3 p-6">
          {SECTIONS.map((section) => (
            <SectionColumnFilter
              key={section.id}
              section={section}
              selectedColumns={sectionStates[section.id].selectedColumns}
              expanded={sectionStates[section.id].expanded}
              onToggleExpand={() => handleToggleExpand(section.id)}
              onColumnsChange={(cols) => handleColumnsChange(section.id, cols)}
              disabled={isProcessing}
            />
          ))}
        </CardBody>
      </Card>

      {saveMessage && (
        <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-800">
          {saveMessage}
        </p>
      )}

      {settingsChanged && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
          Settings changed. Generate again to update the preview.
        </p>
      )}

      <ActionBar
        onGenerate={onGenerate}
        onReset={() => void handleReset()}
        onSave={() => void onSave()}
        generateDisabled={
          isProcessing || !isDateRangeValid || sectionValidationError !== null
        }
        resetDisabled={false}
        showDownload={false}
        isProcessing={isProcessing}
      />

      <OutputCard
          title="Generated Output"
          description="Download your report after generation"
          status={status}
          manualStatus={manualStatus}
          outputFile={
            status === "completed" && runState
              ? {
                  name:
                    dualOutputMode && runState.pdf_filename
                      ? `${runState.excel_filename ?? "report.xlsx"} · ${runState.pdf_filename}`
                      : runState.excel_filename ??
                        runState.output_filename ??
                        `${downloadTitle.toLowerCase().replace(/\s+/g, "_")}_report`,
                  size: formatFileSize(
                    dualOutputMode
                      ? (runState.excel_file_size ?? runState.output_file_size)
                      : runState.output_file_size,
                  ),
                  generatedAt: runState.generated_at
                    ? new Date(runState.generated_at).toLocaleString()
                    : new Date().toLocaleString(),
                  rowCount: runState.processed_row_count ?? runState.source_row_count ?? undefined,
                  reportDate: runState.report_date ?? undefined,
                }
              : undefined
          }
          errorMessage={errorMessage ?? undefined}
          dualOutputMode={dualOutputMode}
          onPreviewPdf={onPreviewPdf}
          onDownloadPdf={() => void onDownloadPdf()}
          onDownloadExcel={() => void onDownloadExcel()}
          previewPdfDisabled={!canPreviewPdf}
          downloadPdfDisabled={!canDownloadPdf}
          downloadExcelDisabled={!canDownloadExcel}
          disabled={!canDownload}
        />
    </div>
  );
}
