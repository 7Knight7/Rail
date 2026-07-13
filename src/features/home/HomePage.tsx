import { Button } from "@/components/ui/Button";
import { RailMadadLoginDialog } from "@/features/automation/components/RailMadadLoginDialog";
import { HomeGenerationProgress } from "@/features/home/components/HomeGenerationProgress";
import { HomeGenerationTimeline } from "@/features/home/components/HomeGenerationTimeline";
import { HomeQuickActions } from "@/features/home/components/HomeQuickActions";
import { HomeRecentActivity } from "@/features/home/components/HomeRecentActivity";
import { HomeReportsGrid } from "@/features/home/components/HomeReportsGrid";
import { HomeStatsGrid } from "@/features/home/components/HomeStatsGrid";
import { HomeWelcomeSection } from "@/features/home/components/HomeWelcomeSection";
import { STATUS_METRICS } from "@/features/home/homeData";
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

  // Strict gate: progress UI only after an explicit Generate click in this session.
  const started = generation.generationStarted === true;
  const isGenerating =
    started &&
    (generation.runStatus === "running" || generation.runStatus === "paused");
  const showProgress =
    started &&
    (isGenerating ||
      generation.runStatus === "completed" ||
      generation.runStatus === "failed" ||
      generation.isComplete ||
      generation.hasFailed);

  const pipelineStep = pipelineStepFromProgress(
    generation.progressPercent,
    isGenerating,
  );

  if (showProgress && isAdmin) {
    return (
      <>
        <RailMadadLoginDialog
          open={generation.showLoginDialog}
          onClose={generation.onCloseLoginDialog}
        />
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
                onClick={() => void generation.onStop()}
              >
                Cancel generation
              </Button>
            </div>
          )}
        </div>
      </>
    );
  }

  return (
    <>
      <RailMadadLoginDialog
        open={generation.showLoginDialog}
        onClose={generation.onCloseLoginDialog}
      />
      <div className="space-y-12 pb-4">
        <HomeWelcomeSection
          isAdmin={isAdmin}
          isStarting={generation.acting && !showProgress}
          onGenerate={() => void generation.onStart()}
          disabled={generation.selectedReportIds.length === 0}
        />

        <HomeStatsGrid metrics={STATUS_METRICS} />

        <HomeReportsGrid />

        <HomeRecentActivity />

        <HomeQuickActions />
      </div>
    </>
  );
}
