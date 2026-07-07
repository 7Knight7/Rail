import { FileOutput, Download, CheckCircle2, Clock, XCircle } from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";

type OutputStatus = "idle" | "processing" | "completed" | "error";

interface OutputFile {
  name: string;
  size: string;
  generatedAt: string;
}

interface OutputCardProps {
  title?: string;
  description?: string;
  status: OutputStatus;
  outputFile?: OutputFile;
  errorMessage?: string;
  onDownload?: () => void;
  disabled?: boolean;
}

const statusConfig = {
  idle: {
    label: "Waiting",
    variant: "neutral" as const,
    icon: Clock,
  },
  processing: {
    label: "Processing",
    variant: "info" as const,
    icon: Clock,
  },
  completed: {
    label: "Completed",
    variant: "success" as const,
    icon: CheckCircle2,
  },
  error: {
    label: "Error",
    variant: "error" as const,
    icon: XCircle,
  },
};

export function OutputCard({
  title = "Output",
  description = "Generated report will appear here",
  status,
  outputFile,
  errorMessage,
  onDownload,
  disabled = false,
}: OutputCardProps) {
  const config = statusConfig[status];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileOutput className="h-4 w-4 text-slate-500" />
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </div>
          </div>
          <StatusBadge variant={config.variant}>{config.label}</StatusBadge>
        </div>
      </CardHeader>
      <CardBody>
        {status === "idle" && (
          <EmptyState
            icon={FileOutput}
            title="No output yet"
            description="Upload a file and generate to see results"
          />
        )}

        {status === "processing" && (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
            <p className="mt-4 text-sm text-slate-600">Processing your file...</p>
          </div>
        )}

        {status === "completed" && outputFile && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">{outputFile.name}</p>
                <p className="text-xs text-slate-500">
                  {outputFile.size} - Generated at {outputFile.generatedAt}
                </p>
              </div>
            </div>
            <Button
              variant="primary"
              className="w-full"
              onClick={onDownload}
              disabled={disabled}
            >
              <Download className="mr-2 h-4 w-4" />
              Download Report
            </Button>
          </div>
        )}

        {status === "error" && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="flex items-start gap-3">
              <XCircle className="h-5 w-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-800">Processing Failed</p>
                <p className="mt-1 text-xs text-red-600">
                  {errorMessage || "An error occurred while processing the file."}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
