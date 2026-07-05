import { useState, useCallback } from "react";
import { PageHeader } from "@/components/PageHeader";
import { UploadCard } from "./UploadCard";
import { SettingsCard } from "./SettingsCard";
import { PreviewTable } from "./PreviewTable";
import { OutputCard } from "./OutputCard";
import { ActionBar } from "./ActionBar";

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
  title: string;
  description: string;
  breadcrumbs?: { label: string; href?: string }[];
  settingsFields: SettingField[];
  previewColumns: Column[];
  mockPreviewData?: Record<string, string | number>[];
}

export function WorkflowPageLayout({
  title,
  description,
  breadcrumbs = [{ label: "Reports" }, { label: title }],
  settingsFields: initialSettings,
  previewColumns,
  mockPreviewData = [],
}: WorkflowPageLayoutProps) {
  const [file, setFile] = useState<File | null>(null);
  const [settings, setSettings] = useState(initialSettings);
  const [status, setStatus] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const [previewData, setPreviewData] = useState<Record<string, string | number>[]>([]);

  const handleFileSelect = useCallback((selectedFile: File) => {
    setFile(selectedFile);
    setPreviewData(mockPreviewData);
    setStatus("idle");
  }, [mockPreviewData]);

  const handleFileRemove = useCallback(() => {
    setFile(null);
    setPreviewData([]);
    setStatus("idle");
  }, []);

  const handleSettingChange = useCallback((id: string, value: string | number) => {
    setSettings((prev) =>
      prev.map((field) => (field.id === id ? { ...field, value } : field)),
    );
  }, []);

  const handleGenerate = useCallback(() => {
    setStatus("processing");
    setTimeout(() => {
      setStatus("completed");
    }, 2000);
  }, []);

  const handleReset = useCallback(() => {
    setFile(null);
    setPreviewData([]);
    setStatus("idle");
    setSettings(initialSettings);
  }, [initialSettings]);

  const handleDownload = useCallback(() => {
    alert("Download functionality will be implemented with business logic.");
  }, []);

  return (
    <div>
      <PageHeader title={title} description={description} breadcrumbs={breadcrumbs} />

      <div className="grid gap-6 lg:grid-cols-2">
        <SettingsCard
          title="Report Settings"
          description="Configure parameters for this report"
          fields={settings}
          onChange={handleSettingChange}
          disabled={status === "processing"}
        />

        <UploadCard
          title="Upload Data"
          description="Upload your Excel or CSV file"
          onFileSelect={handleFileSelect}
          onFileRemove={handleFileRemove}
          disabled={status === "processing"}
        />
      </div>

      <div className="mt-6">
        <ActionBar
          onGenerate={handleGenerate}
          onReset={handleReset}
          onDownload={handleDownload}
          generateDisabled={!file}
          resetDisabled={!file && status === "idle"}
          downloadDisabled={status !== "completed"}
          isProcessing={status === "processing"}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <PreviewTable
          title="Data Preview"
          description="Preview of uploaded data"
          columns={previewColumns}
          data={previewData}
          emptyMessage="Upload a file to preview data"
        />

        <OutputCard
          title="Generated Report"
          description="Your report will appear here after processing"
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
