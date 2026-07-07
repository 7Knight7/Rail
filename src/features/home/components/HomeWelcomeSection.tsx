import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { getTimeGreeting } from "@/layouts/TopBar";
import { Button } from "@/components/ui/Button";

interface HomeWelcomeSectionProps {
  isAdmin: boolean;
  isStarting: boolean;
  onGenerate: () => void;
  disabled?: boolean;
}

export function HomeWelcomeSection({
  isAdmin,
  isStarting,
  onGenerate,
  disabled,
}: HomeWelcomeSectionProps) {
  const { user } = useAuth();
  const name = user?.username?.split(/[\s_-]/)[0] ?? "Officer";

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-medium text-rail-muted">
          {getTimeGreeting()}, {name}
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-rail-ink lg:text-4xl">
          Generate Today&apos;s Reports
        </h1>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-rail-muted">
          Generate all scheduled RailMadad reports with a single click. Your dashboard,
          analytics and report files will automatically be updated.
        </p>
      </div>

      {isAdmin ? (
        <Button
          size="lg"
          className="h-12 rounded-xl px-8 text-base shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-premium active:scale-[0.98]"
          onClick={onGenerate}
          disabled={disabled || isStarting}
        >
          {isStarting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Starting generation…
            </>
          ) : (
            "Generate Today's Reports"
          )}
        </Button>
      ) : (
        <p className="text-sm text-rail-muted">
          Contact your administrator to generate today&apos;s reports.
        </p>
      )}
    </section>
  );
}
