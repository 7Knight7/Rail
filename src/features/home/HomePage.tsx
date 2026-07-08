import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { HomeGenerationProgress } from "@/features/home/components/HomeGenerationProgress";
import { HomeGenerationTimeline } from "@/features/home/components/HomeGenerationTimeline";
import { HomeQuickActions } from "@/features/home/components/HomeQuickActions";
import { HomeRecentActivity } from "@/features/home/components/HomeRecentActivity";
import { HomeReportsGrid } from "@/features/home/components/HomeReportsGrid";
import { HomeStatsGrid } from "@/features/home/components/HomeStatsGrid";
import { HomeWelcomeSection } from "@/features/home/components/HomeWelcomeSection";
import { useHomeOverview } from "@/features/home/hooks/useHomeOverview";
import { useAutomationPage } from "@/features/automation/hooks/useAutomationPage";
import { usePermissions } from "@/hooks/usePermissions";

function pipelineStepFromProgress(percent: number, isRunning: boolean): number {
  if (!isRunning) return 0;
  if (percent >= 100) return 5;
  if (percent >= 75) return 4;
  if (percent >= 50) return 3;
  if (percent >= 25) return 2;
  return 1;
}

export function HomePage() {
  const { isAdmin } = usePermissions();
  const generation = useAutomationPage();
  const { data: overview, metrics, loading: overviewLoading } = useHomeOverview();

  const isGenerating =
    generation.isBusy ||
    generation.runStatus === "running" ||
    generation.runStatus === "paused";
  const showProgress =
    isGenerating || generation.isComplete || generation.hasFailed;

  const pipelineStep = pipelineStepFromProgress(
    generation.progressPercent,
    isGenerating,
  );

  if (generation.loading && isAdmin) {
    return (
      <div className="flex justify-center py-32">
        <Spinner size="lg" />
      </div>
    );
  }

  if (showProgress && isAdmin) {
    return (
      <div className="animate-fade-in space-y-8">
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <HomeGenerationProgress
              steps={generation.steps}
              progressPercent={generation.progressPercent}
              isBusy={generation.isBusy}
              isPaused={generation.isPaused}
              hasFailed={generation.hasFailed}
              isComplete={generation.isComplete}
              acting={generation.acting}
              onPause={generation.onPause}
              onResume={generation.onResume}
              onStop={generation.onStop}
            />
          </div>
          <div className="lg:col-span-2">
            <HomeGenerationTimeline activeStep={pipelineStep} isRunning={isGenerating} />
          </div>
        </div>
        {!generation.isComplete && (
          <div className="flex justify-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={generation.onStop}
              disabled={generation.acting || !generation.isBusy}
            >
              Cancel generation
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-12 pb-4">
      <HomeWelcomeSection
        isAdmin={isAdmin}
        isStarting={generation.acting}
        onGenerate={() => void generation.onStart()}
        disabled={generation.selectedReportIds.length === 0}
      />

      <HomeStatsGrid metrics={metrics} loading={overviewLoading} />

      <HomeReportsGrid reports={overview?.reports ?? []} loading={overviewLoading} />

      <HomeRecentActivity
        items={overview?.recentActivity ?? []}
        loading={overviewLoading}
      />

      <HomeQuickActions />
    </div>
  );
}
