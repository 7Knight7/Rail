import { Play, RotateCcw, Download } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface ActionBarProps {
  onGenerate?: () => void;
  onReset?: () => void;
  onDownload?: () => void;
  generateDisabled?: boolean;
  resetDisabled?: boolean;
  downloadDisabled?: boolean;
  isProcessing?: boolean;
}

export function ActionBar({
  onGenerate,
  onReset,
  onDownload,
  generateDisabled = false,
  resetDisabled = false,
  downloadDisabled = true,
  isProcessing = false,
}: ActionBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <Button
        variant="primary"
        onClick={onGenerate}
        disabled={generateDisabled || isProcessing}
      >
        <Play className="mr-2 h-4 w-4" />
        {isProcessing ? "Processing..." : "Generate Report"}
      </Button>
      <Button variant="secondary" onClick={onReset} disabled={resetDisabled || isProcessing}>
        <RotateCcw className="mr-2 h-4 w-4" />
        Reset
      </Button>
      <div className="flex-1" />
      <Button
        variant="secondary"
        onClick={onDownload}
        disabled={downloadDisabled || isProcessing}
      >
        <Download className="mr-2 h-4 w-4" />
        Download
      </Button>
    </div>
  );
}
