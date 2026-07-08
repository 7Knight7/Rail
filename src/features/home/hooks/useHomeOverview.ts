import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { Clock, FileCheck, Layers, Timer } from "lucide-react";
import {
  fetchHomeOverview,
  type HomeOverviewResponse,
  type HomeStatMetric,
} from "@/api/home";

const STAT_ICONS: Record<string, LucideIcon> = {
  "Last Generated": Clock,
  "Reports Available": FileCheck,
  "Generated Today": Timer,
  "Open Cases": Layers,
};

export interface HomeStatWithIcon extends HomeStatMetric {
  icon: LucideIcon;
  accent?: boolean;
}

export function useHomeOverview() {
  const [data, setData] = useState<HomeOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchHomeOverview()
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load home overview");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const metrics: HomeStatWithIcon[] =
    data?.stats.map((stat) => ({
      ...stat,
      icon: STAT_ICONS[stat.title] ?? FileCheck,
      accent: stat.title === "Open Cases",
    })) ?? [];

  return { data, metrics, loading, error };
}
