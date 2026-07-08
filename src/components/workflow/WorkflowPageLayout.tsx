import { useState, useCallback, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SettingsCard } from "./SettingsCard";
import { PreviewTable } from "./PreviewTable";
import { OutputCard } from "./OutputCard";
import { ActionBar } from "./ActionBar";
import { cn } from "@/utils/cn";
import {
  FilterBuilder,
  VisibleColumnsSection,
  useDatasetMetadata,
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
  mockPreviewData?: Record<string, string | number>[];
}

export function WorkflowPageLayout({
  reportId,
  title,
  description,
  breadcrumbs = [{ label: "Report Configuration" }, { label: title }],
  settingsFields: initialSettings,
  advancedFields: initialAdvanced = [],
  previewColumns,
  mockPreviewData = [],
}: WorkflowPageLayoutProps) {
  const { metadata, loading: metadataLoading, error: metadataError } = useDatasetMetadata(reportId);
  const [settings, setSettings] = useState(initialSettings);
  const [advancedSettings, setAdvancedSettings] = useState(initialAdvanced);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [status, setStatus] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const [previewData, setPreviewData] = useState<Record<string, string | number>[]>([]);
  const [filterConditions, setFilterConditions] = useState<FilterCondition[]>([]);
  const [visibleColumnIds, setVisibleColumnIds] = useState<string[]>([]);

  useEffect(() => {
    if (!metadata?.columns.length) return;
    setVisibleColumnIds((current) =>
      current.length > 0 ? current : metadata.columns.map((column: ColumnMetadata) => column.id),
    );
  }, [metadata]);

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

  const handleGenerate = useCallback(() => {
    setStatus("processing");
    setTimeout(() => {
      setStatus("completed");
      setPreviewData(mockPreviewData);
    }, 2000);
  }, [mockPreviewData]);

  const handleSaveConfiguration = useCallback(() => {
    alert("Configuration saved.");
  }, []);

  const handleReset = useCallback(() => {
    setPreviewData([]);
    setStatus("idle");
    setSettings(initialSettings);
    setAdvancedSettings(initialAdvanced);
    setFilterConditions([]);
    setVisibleColumnIds(metadata?.columns.map((column: ColumnMetadata) => column.id) ?? []);
  }, [initialAdvanced, initialSettings, metadata]);

  const handleDownload = useCallback(() => {
    alert("Download will be available after report generation.");
  }, []);

  const datasetSourceLabel = metadata?.sourceFilename ?? "Original RailMadad dataset";

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
                Source dataset: <span className="font-medium text-slate-700">{datasetSourceLabel}</span>
                {metadata ? ` · ${metadata.columns.length} original columns` : ""}
              </p>
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
        generateDisabled={false}
        resetDisabled={status === "idle" && previewData.length === 0}
        downloadDisabled={status !== "completed"}
        isProcessing={status === "processing"}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PreviewTable
          title="Report Preview"
          description="Preview of today's generated report"
          columns={previewColumns}
          data={previewData}
          emptyMessage="No preview available. Generate the report to preview today's output."
        />

        <OutputCard
          title="Generated Output"
          description="Download your report after generation"
          status={status}
          outputFile={
            status === "completed"
              ? {
                  name: `${title.toLowerCase().replace(/\s+/g, "_")}_report.xlsx`,
                  size: "2.4 MB",
                  generatedAt: new Date().toLocaleString(),
                }
              : undefined
          }
          onDownload={handleDownload}
        />
      </div>
    </div>
  );
}
