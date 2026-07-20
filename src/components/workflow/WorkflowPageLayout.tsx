import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { ChevronDown } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SettingsCard } from "./SettingsCard";
import { PreviewTable } from "./PreviewTable";
import { SectionedPreviewTable } from "./SectionedPreviewTable";
import { OutputCard } from "./OutputCard";
import { ActionBar } from "./ActionBar";
import { useManualReportGeneration } from "./useManualReportGeneration";
import { cn } from "@/utils/cn";
import { formatFileSize, reportsApi } from "@/api/reports";
import {
  FilterBuilder,
  VisibleColumnsSection,
  GroupedOutputColumnsSection,
  useDatasetMetadata,
  useOutputColumnCatalog,
  usesOutputColumnCatalog,
  useReactiveOutputPreview,
  usesReactiveOutputPreview,
  type FilterCondition,
  type ReportId,
  type ColumnMetadata,
} from "@/features/report-config";

interface SettingField {
  id: string;
  label: string;
  type: "text" | "number" | "select" | "date";
  value: string | number;
  options?: { value: string; label: string }[];
  placeholder?: string;
}

interface Column {
  key: string;
  header: string;
  width?: string;
}

interface WorkflowPageLayoutProps {
  reportId: ReportId;
  title: string;
  description: string;
  breadcrumbs?: { label: string; href?: string }[];
  settingsFields: SettingField[];
  advancedFields?: SettingField[];
  previewColumns?: Column[];
  mockPreviewData?: Record<string, string | number>[];
}

function previousDayIsoDate(): string {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  return date.toISOString().split("T")[0];
}

export function WorkflowPageLayout({
  reportId,
  title,
  description,
  breadcrumbs = [{ label: "Report Configuration" }, { label: title }],
  settingsFields: initialSettings,
  advancedFields: initialAdvanced = [],
  previewColumns: defaultPreviewColumns = [],
}: WorkflowPageLayoutProps) {
  const outputCatalogMode = usesOutputColumnCatalog(reportId);
  const reactivePreviewMode = usesReactiveOutputPreview(reportId);
  const { metadata, loading: metadataLoading, error: metadataError } = useDatasetMetadata(reportId);
  const {
    columns: outputColumns,
    defaultColumnIds,
    loading: outputLoading,
    error: outputError,
  } = useOutputColumnCatalog(reportId);
  const columnPickerColumns = outputCatalogMode ? outputColumns : metadata?.columns ?? [];
  const columnPickerLoading = outputCatalogMode ? outputLoading : metadataLoading;
  const columnPickerError = outputCatalogMode ? outputError : metadataError;
  const [settings, setSettings] = useState(() =>
    initialSettings.map((field) =>
      field.id === "reportDate" ? { ...field, value: previousDayIsoDate() } : field,
    ),
  );
  const [advancedSettings, setAdvancedSettings] = useState(initialAdvanced);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [filterConditions, setFilterConditions] = useState<FilterCondition[]>([]);
  const [visibleColumnIds, setVisibleColumnIds] = useState<string[]>([]);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const userTouchedColumnsRef = useRef(false);

  const columnLabelMap = useMemo(
    () =>
      Object.fromEntries(
        columnPickerColumns.map((column: ColumnMetadata) => [
          column.id,
          column.displayName,
        ]),
      ),
    [columnPickerColumns],
  );

  const handleVisibleColumnIdsChange = useCallback((next: string[]) => {
    userTouchedColumnsRef.current = true;
    if (reportId === "merging") {
      console.info("report1_selected_columns_changed", {
        selected_column_ids: next,
        count: next.length,
      });
    } else if (reportId === "division") {
      console.info("report2_selected_columns_changed", {
        selected_column_ids: next,
        count: next.length,
      });
    }
    setVisibleColumnIds(next);
  }, [reportId]);

  const {
    status,
    manualStatus,
    runState,
    previewData,
    previewColumns: dynamicPreviewColumns,
    errorMessage,
    handleGenerate,
    handleSaveConfiguration,
    handleDownload,
    handleDownloadExcel,
    handleDownloadPdf,
    handlePreviewPdf,
    resetGeneration,
    canDownload,
    canDownloadExcel,
    canDownloadPdf,
    canPreviewPdf,
    dualOutputMode,
  } = useManualReportGeneration({
    reportId,
    visibleColumnIds,
    columnLabels: columnLabelMap,
    filterConditions,
    settings,
  });

  const reactivePreview = useReactiveOutputPreview({
    reportId,
    selectedColumnIds: visibleColumnIds,
    enabled: reactivePreviewMode && status !== "processing",
  });

  useEffect(() => {
    if (outputCatalogMode) {
      if (!outputColumns.length) return;
      setVisibleColumnIds((current) =>
        current.length > 0
          ? current
          : defaultColumnIds.length > 0
            ? defaultColumnIds
            : outputColumns.map((column: ColumnMetadata) => column.id),
      );
      return;
    }
    if (!metadata?.columns.length) return;
    setVisibleColumnIds((current) =>
      current.length > 0 ? current : metadata.columns.map((column: ColumnMetadata) => column.id),
    );
  }, [metadata, outputCatalogMode, outputColumns, defaultColumnIds]);

  useEffect(() => {
    let cancelled = false;
    void reportsApi.loadConfig(reportId).then((saved) => {
      if (cancelled || !saved) return;
      if (saved.selected_column_ids?.length && !userTouchedColumnsRef.current) {
        setVisibleColumnIds(saved.selected_column_ids);
      }
      if (saved.export_format) {
        setSettings((prev) =>
          prev.map((field) =>
            field.id === "exportFormat" ? { ...field, value: saved.export_format } : field,
          ),
        );
      }
      if (saved.filter_conditions?.length) {
        setFilterConditions(saved.filter_conditions as FilterCondition[]);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [reportId]);

  const handleSettingChange = useCallback((id: string, value: string | number) => {
    setSettings((prev) =>
      prev.map((field) => (field.id === id ? { ...field, value } : field)),
    );
  }, []);

  const handleAdvancedChange = useCallback((id: string, value: string | number) => {
    setAdvancedSettings((prev) =>
      prev.map((field) => (field.id === id ? { ...field, value } : field)),
    );
  }, []);

  const handleSave = useCallback(async () => {
    try {
      await handleSaveConfiguration();
      setSaveMessage("Configuration saved.");
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save configuration.");
    }
  }, [handleSaveConfiguration]);

  const handleReset = useCallback(() => {
    resetGeneration();
    setSettings(
      initialSettings.map((field) =>
        field.id === "reportDate" ? { ...field, value: previousDayIsoDate() } : field,
      ),
    );
    setAdvancedSettings(initialAdvanced);
    setFilterConditions([]);
    if (outputCatalogMode) {
      setVisibleColumnIds(
        defaultColumnIds.length > 0
          ? defaultColumnIds
          : outputColumns.map((column: ColumnMetadata) => column.id),
      );
    } else {
      setVisibleColumnIds(metadata?.columns.map((column: ColumnMetadata) => column.id) ?? []);
    }
  }, [initialAdvanced, initialSettings, metadata, outputCatalogMode, outputColumns, defaultColumnIds, resetGeneration]);

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

  const onDownload = useCallback(async () => {
    try {
      const { blob, filename } = await handleDownload();
      triggerBlobDownload(blob, filename);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed.");
    }
  }, [handleDownload, triggerBlobDownload]);

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

  const datasetSourceLabel = metadata?.sourceFilename ?? "Original RailMadad dataset";
  const runPreviewColumns =
    dynamicPreviewColumns.length > 0 ? dynamicPreviewColumns : defaultPreviewColumns;
  const activePreviewColumns = reactivePreviewMode
    ? reactivePreview.previewColumns.length > 0
      ? reactivePreview.previewColumns
      : runPreviewColumns
    : runPreviewColumns;
  const activePreviewData = reactivePreviewMode
    ? reactivePreview.previewData.length > 0
      ? reactivePreview.previewData
      : previewData
    : previewData;
  const previewEmptyMessage = reactivePreviewMode
    ? reactivePreview.emptyMessage ||
      "No generated report data is available for preview."
    : "No preview available. Generate the report to preview processed output.";
  const reportDateLabel = runState?.report_date ?? previousDayIsoDate().split("-").reverse().join("-");

  return (
    <div className="space-y-8">
      <PageHeader title={title} description={description} breadcrumbs={breadcrumbs} />

      <SettingsCard
        title="Report Settings"
        description="Configure how this report should be generated"
        fields={settings}
        onChange={handleSettingChange}
        disabled={status === "processing"}
      />

      <div className="overflow-hidden rounded-2xl border border-rail-line bg-white shadow-card transition-all duration-200 hover:shadow-premium">
        <button
          type="button"
          onClick={() => setAdvancedOpen((open) => !open)}
          className="flex w-full items-center justify-between px-6 py-5 text-left transition-colors hover:bg-surface/50"
        >
          <div>
            <span className="text-sm font-semibold text-slate-900">Advanced Settings</span>
            <p className="mt-0.5 text-xs text-slate-500">
              Dynamic filters, visible columns, highlights and export options
            </p>
          </div>
          <ChevronDown
            className={cn(
              "h-4 w-4 shrink-0 text-slate-400 transition-transform duration-200",
              advancedOpen && "rotate-180",
            )}
          />
        </button>

        {advancedOpen && (
          <div className="space-y-6 border-t border-rail-line px-6 py-6">
            <div className="rounded-xl border border-rail-line bg-white p-4">
              <p className="text-xs text-slate-500">
                {outputCatalogMode ? (
                  <>
                    Output columns:{" "}
                    <span className="font-medium text-slate-700">
                      {columnPickerColumns.length} selectable fields
                    </span>
                  </>
                ) : (
                  <>
                    Source dataset:{" "}
                    <span className="font-medium text-slate-700">{datasetSourceLabel}</span>
                    {metadata ? ` · ${metadata.columns.length} original columns` : ""}
                  </>
                )}
              </p>
            </div>

            {!outputCatalogMode && (
              <FilterBuilder
                columns={metadata?.columns ?? []}
                conditions={filterConditions}
                onChange={setFilterConditions}
                loading={metadataLoading}
                error={metadataError}
                disabled={status === "processing"}
              />
            )}

            <div className={outputCatalogMode ? "" : "border-t border-rail-line pt-6"}>
              {reactivePreviewMode ? (
                <GroupedOutputColumnsSection
                  columns={columnPickerColumns}
                  selectedColumnIds={visibleColumnIds}
                  defaultColumnIds={defaultColumnIds}
                  onChange={handleVisibleColumnIdsChange}
                  disabled={status === "processing" || columnPickerLoading}
                />
              ) : (
                <VisibleColumnsSection
                  columns={columnPickerColumns}
                  selectedColumnIds={visibleColumnIds}
                  onChange={handleVisibleColumnIdsChange}
                  disabled={status === "processing" || columnPickerLoading}
                />
              )}
              {columnPickerError ? (
                <p className="mt-2 text-xs text-danger">{columnPickerError}</p>
              ) : null}
            </div>

            {advancedSettings.length > 0 && (
              <div className="border-t border-rail-line pt-2">
                <SettingsCard
                  title=""
                  description="Highlight rules and export options"
                  fields={advancedSettings}
                  onChange={handleAdvancedChange}
                  disabled={status === "processing"}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {saveMessage && (
        <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-800">
          {saveMessage}
        </p>
      )}

      <ActionBar
        onGenerate={() => void handleGenerate()}
        onReset={handleReset}
        onDownload={() => void onDownload()}
        onSave={() => void handleSave()}
        generateDisabled={status === "processing" || visibleColumnIds.length === 0}
        resetDisabled={status === "idle" && previewData.length === 0}
        downloadDisabled={!canDownload}
        showDownload={!dualOutputMode}
        isProcessing={status === "processing"}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {reactivePreviewMode && reportId === "types" && reactivePreview.previewSections.length > 0 ? (
          <SectionedPreviewTable
            title="Report Preview"
            description={`Preview of generated report (report date ${reportDateLabel})`}
            sections={reactivePreview.previewSections}
            emptyMessage={previewEmptyMessage}
          />
        ) : (
          <PreviewTable
            title="Report Preview"
            description={`Preview of generated report (report date ${reportDateLabel})`}
            columns={activePreviewColumns}
            data={activePreviewData}
            emptyMessage={previewEmptyMessage}
          />
        )}

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
                        `${title.toLowerCase().replace(/\s+/g, "_")}_report`,
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
          onDownload={() => void onDownload()}
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
    </div>
  );
}
