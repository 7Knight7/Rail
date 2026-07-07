import { Link } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import type { AutomationCompletionSummary } from "@/features/automation/types/automation";
import { formatDuration } from "@/features/automation/utils/display";

export interface AutomationCompletionSummaryProps {
  summary: AutomationCompletionSummary;
}

export function AutomationCompletionSummaryCard({ summary }: AutomationCompletionSummaryProps) {
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
