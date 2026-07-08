import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { ChevronDown, Upload } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SettingsCard } from "./SettingsCard";
import { PreviewTable } from "./PreviewTable";
import { OutputCard } from "./OutputCard";
import { ActionBar } from "./ActionBar";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";
import { cn } from "@/utils/cn";
import { datasetsApi } from "@/api/datasets";
import { previewProcessedDataset } from "@/api/processing";
import { saveReportConfig, fetchSavedReportConfig } from "@/api/reportConfigs";
import { uploadDatasetFile } from "@/api/uploads";
import {
  formatFileSize,
  generateOutputs,
  getOutputDownloadUrl,
  type GenerateOutputsResponse,
} from "@/api/outputs";
import { useWorkflowSession } from "@/context/WorkflowSessionContext";
import { REPORT_ID_TO_SOURCE } from "@/features/workflows/reportSourceMap";
import {
  FilterBuilder,
  VisibleColumnsSection,
  useDatasetMetadata,
  buildPreviewColumns,
  buildReportConfiguration,
  getExportOptions,
  applySavedConfiguration,
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
  previewColumns: Column[];
}

export function WorkflowPageLayout({
  reportId,
  title,
  description,
  breadcrumbs = [{ label: "Report Configuration" }, { label: title }],
  settingsFields: initialSettings,
  advancedFields: initialAdvanced = [],
  previewColumns,
}: WorkflowPageLayoutProps) {
  const { metadata, loading: metadataLoading, error: metadataError, refresh } =
    useDatasetMetadata(reportId);
  const { markReportComplete } = useWorkflowSession();
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [settings, setSettings] = useState(initialSettings);
  const [advancedSettings, setAdvancedSettings] = useState(initialAdvanced);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [status, setStatus] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const [previewData, setPreviewData] = useState<Record<string, string | number>[]>([]);
  const [filterConditions, setFilterConditions] = useState<FilterCondition[]>([]);
  const [visibleColumnIds, setVisibleColumnIds] = useState<string[]>([]);
  const [outputResult, setOutputResult] = useState<GenerateOutputsResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [savedConfigLoaded, setSavedConfigLoaded] = useState(false);

  useEffect(() => {
    if (!metadata?.columns.length) return;
    setVisibleColumnIds((current) =>
      current.length > 0 ? current : metadata.columns.map((column: ColumnMetadata) => column.id),
    );
  }, [metadata]);

  useEffect(() => {
    if (!metadata?.columns.length || savedConfigLoaded) return;

    let cancelled = false;
    fetchSavedReportConfig(reportId)
      .then((saved) => {
        if (cancelled || !saved?.configuration) return;
        const applied = applySavedConfiguration(
          saved.configuration,
          metadata.columns,
          initialSettings,
          initialAdvanced,
        );
        setSettings((current) =>
          current.map((field) => {
            const updated = applied.settings.find((item) => item.id === field.id);
            return updated ? { ...field, value: updated.value } : field;
          }),
        );
        setAdvancedSettings((current) =>
          current.map((field) => {
            const updated = applied.advancedSettings.find((item) => item.id === field.id);
            return updated ? { ...field, value: updated.value } : field;
          }),
        );
        setFilterConditions(applied.filterConditions);
        setVisibleColumnIds(applied.visibleColumnIds);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setSavedConfigLoaded(true);
      });

    return () => {
      cancelled = true;
    };
  }, [initialAdvanced, initialSettings, metadata?.columns, reportId, savedConfigLoaded]);

  const activePreviewColumns = useMemo(
    () => buildPreviewColumns(outputResult?.processed.columns, previewColumns),
    [outputResult?.processed.columns, previewColumns],
  );

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

  const buildConfiguration = useCallback(() => {
    if (!metadata?.columns.length) {
      throw new Error("Dataset metadata is not available yet.");
    }

    return buildReportConfiguration({
      reportId,
      settings,
      advancedSettings,
      filterConditions,
      visibleColumnIds,
      columns: metadata.columns,
    });
  }, [advancedSettings, filterConditions, metadata?.columns, reportId, settings, visibleColumnIds]);

  const handleGenerate = useCallback(async () => {
    setStatus("processing");
    setErrorMessage(null);
    setOutputResult(null);

    try {
      const configuration = buildConfiguration();
      const exportOptions = getExportOptions(settings);
      const reportDate = settings.find((field) => field.id === "reportDate")?.value;

      const processed = await previewProcessedDataset({
        reportId,
        configuration,
      });

      const outputs = await generateOutputs({
        reportId,
        reportName: title,
        processed,
        configuration,
        ...exportOptions,
        period: reportDate ? String(reportDate) : undefined,
      });

      setOutputResult(outputs);
      setPreviewData(
        outputs.processed.rows.map((row) => {
          const mapped: Record<string, string | number> = {};
          for (const column of outputs.processed.columns) {
            const value = row[column.name];
            mapped[column.name] =
              typeof value === "number" || typeof value === "string" ? value : String(value ?? "");
          }
          return mapped;
        }),
      );
      setStatus("completed");

      const sourceId = REPORT_ID_TO_SOURCE[reportId];
      if (sourceId) {
        markReportComplete(sourceId);
      }

      showToast("success", "Report generated", `${title} is ready for download.`);
    } catch (error) {
      setStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Report generation failed");
      setPreviewData([]);
      showToast("error", "Generation failed", error instanceof Error ? error.message : undefined);
    }
  }, [buildConfiguration, markReportComplete, reportId, settings, showToast, title]);

  const handleSaveConfiguration = useCallback(async () => {
    setSavingConfig(true);
    try {
      const configuration = buildConfiguration();
      await saveReportConfig(reportId, configuration);
      showToast("success", "Configuration saved");
    } catch (error) {
      showToast(
        "error",
        "Save failed",
        error instanceof Error ? error.message : "Could not save configuration.",
      );
    } finally {
      setSavingConfig(false);
    }
  }, [buildConfiguration, reportId, showToast]);

  const handleUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      setUploading(true);
      try {
        const upload = await uploadDatasetFile(file);
        await datasetsApi.ingestUpload(reportId, { uploadId: upload.id });
        await refresh();
        showToast("success", "Dataset uploaded", `${file.name} ingested successfully.`);
      } catch (error) {
        showToast(
          "error",
          "Upload failed",
          error instanceof Error ? error.message : "Could not ingest dataset.",
        );
      } finally {
        setUploading(false);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    },
    [refresh, reportId, showToast],
  );

  const handleReset = useCallback(() => {
    setPreviewData([]);
    setStatus("idle");
    setOutputResult(null);
    setErrorMessage(null);
    setSettings(initialSettings);
    setAdvancedSettings(initialAdvanced);
    setFilterConditions([]);
    setVisibleColumnIds(metadata?.columns.map((column: ColumnMetadata) => column.id) ?? []);
    setSavedConfigLoaded(false);
  }, [initialAdvanced, initialSettings, metadata]);

  const handleDownload = useCallback(() => {
    if (!outputResult) return;

    const exportFormat = String(settings.find((field) => field.id === "exportFormat")?.value ?? "xlsx");
    const format =
      exportFormat === "pdf" ? "pdf" : exportFormat === "csv" ? "csv" : "excel";
    const artifact = outputResult.artifacts.find((item) => item.format === format);
    if (!artifact) return;

    window.open(getOutputDownloadUrl(outputResult.batchId, format), "_blank", "noopener,noreferrer");
  }, [outputResult, settings]);

  const datasetSourceLabel = metadata?.sourceFilename ?? "Original RailMadad dataset";
  const primaryArtifact = outputResult?.artifacts.find((artifact) => {
    const exportFormat = String(settings.find((field) => field.id === "exportFormat")?.value ?? "xlsx");
    if (exportFormat === "pdf") return artifact.format === "pdf";
    if (exportFormat === "csv") return artifact.format === "csv";
    return artifact.format === "excel";
  });

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
              Dataset upload, filters, visible columns, highlights and export options
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
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-slate-500">
                  Source dataset: <span className="font-medium text-slate-700">{datasetSourceLabel}</span>
                  {metadata ? ` · ${metadata.columns.length} original columns` : ""}
                </p>
                <div className="flex items-center gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    className="hidden"
                    onChange={handleUpload}
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={uploading || status === "processing"}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {uploading ? (
                      <Spinner size="sm" />
                    ) : (
                      <>
                        <Upload className="mr-2 h-4 w-4" />
                        Upload dataset
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>

            <FilterBuilder
              columns={metadata?.columns ?? []}
              conditions={filterConditions}
              onChange={setFilterConditions}
              loading={metadataLoading}
              error={metadataError}
              disabled={status === "processing"}
            />

            <div className="border-t border-rail-line pt-6">
              <VisibleColumnsSection
                columns={metadata?.columns ?? []}
                selectedColumnIds={visibleColumnIds}
                onChange={setVisibleColumnIds}
                disabled={status === "processing" || metadataLoading}
              />
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

      <ActionBar
        onGenerate={handleGenerate}
        onReset={handleReset}
        onDownload={handleDownload}
        onSave={handleSaveConfiguration}
        generateDisabled={metadataLoading || !metadata}
        resetDisabled={status === "idle" && previewData.length === 0}
        downloadDisabled={status !== "completed"}
        isProcessing={status === "processing" || savingConfig}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PreviewTable
          title="Report Preview"
          description="Preview of today's generated report"
          columns={activePreviewColumns}
          data={previewData}
          emptyMessage="No preview available. Generate the report to preview today's output."
        />

        <OutputCard
          title="Generated Output"
          description="Final Excel, PDF, CSV, and dashboard JSON generated on the backend"
          status={status}
          outputFile={
            status === "completed" && outputResult
              ? {
                  name:
                    primaryArtifact?.filename ??
                    `${title.toLowerCase().replace(/\s+/g, "_")}_report`,
                  size: formatFileSize(primaryArtifact?.size ?? 0),
                  generatedAt: new Date(outputResult.generatedAt).toLocaleString(),
                }
              : undefined
          }
          errorMessage={errorMessage ?? undefined}
          onDownload={handleDownload}
        />
      </div>
    </div>
  );
}
