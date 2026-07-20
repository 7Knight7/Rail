import { AlertTriangle, Copy } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

const CHROME_COMMAND = `Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
& "$env:ProgramFiles\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="$env:LOCALAPPDATA\\Google\\Chrome\\User Data" --profile-directory="Default"`;

interface ChromeConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  detail?: string | null;
}

export function ChromeConnectionDialog({ open, onClose, detail }: ChromeConnectionDialogProps) {
  const { showToast } = useToast();

  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText(CHROME_COMMAND);
      showToast("success", "Copied", "Chrome start command copied to clipboard");
    } catch {
      showToast("error", "Copy failed", "Could not copy to clipboard");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-amber-500" />
            <DialogTitle>Chrome Connection Required</DialogTitle>
          </div>
          <DialogDescription className="space-y-3 pt-2">
            <p>
              Report automation connects to your Chrome window on port{" "}
              <strong>9222</strong>. Normal Chrome does not enable this automatically.
            </p>
            <ol className="list-decimal space-y-1 pl-5 text-sm">
              <li>Close all Chrome windows.</li>
              <li>
                Run in PowerShell from the project folder:{" "}
                <code className="rounded bg-slate-100 px-1">.\scripts\start-chrome-debug.ps1</code>
              </li>
              <li>Log in to RailMadad in that Chrome window.</li>
              <li>Click Generate again.</li>
            </ol>
            {detail ? (
              <p className="rounded-md bg-red-50 p-2 text-xs text-red-800">{detail}</p>
            ) : null}
            <pre className="max-h-32 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
              {CHROME_COMMAND}
            </pre>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="secondary" onClick={() => void copyCommand()}>
            <Copy className="mr-2 h-4 w-4" />
            Copy command
          </Button>
          <Button onClick={onClose}>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
