import { useCallback, useEffect, useMemo, useState } from "react";
import {
  summaryApi,
  SUMMARY_TYPE_LABELS,
  type GeneratedSummaryResult,
  type PromptTemplateListItem,
  type SummaryType,
} from "@/api/summary";
import { fetchGeneratedReports } from "@/api/outputs";
import { previewProcessedDataset } from "@/api/processing";
import { fetchSavedReportConfig } from "@/api/reportConfigs";
import { useToast } from "@/components/ui/Toast";
import { useWorkflowSession } from "@/context/WorkflowSessionContext";
import {
  REPORT_ID_TO_SOURCE,
  SUMMARY_REPORT_OPTIONS,
} from "@/features/workflows/reportSourceMap";
import type { ReportId } from "@/features/report-config/types";
import type { GeneratedSummary, ReportSourceId } from "@/types/workflow";

const SUMMARY_TYPES: SummaryType[] = [
  "executive",
  "whatsapp",
  "email",
  "daily_highlights",
  "key_observations",
];

function mapResultToSection(
  summaries: Partial<Record<SummaryType, GeneratedSummaryResult>>,
): GeneratedSummary | null {
  if (Object.keys(summaries).length === 0) return null;
  const first = Object.values(summaries)[0];
  return {
    id: first?.id ?? "",
    executive: summaries.executive?.content ?? "",
    whatsapp: summaries.whatsapp?.content ?? "",
    email: summaries.email?.content ?? "",
    dailyHighlights: summaries.daily_highlights?.content ?? "",
    keyObservations: summaries.key_observations?.content ?? "",
    statistics: first?.statistics as unknown as Record<string, unknown>,
    generatedAt: first?.created_at,
  };
}

async function buildDatasetForReports(
  selected: ReportSourceId[],
): Promise<Record<string, unknown>[]> {
  const rows: Record<string, unknown>[] = [];

  for (const sourceId of selected) {
    const option = SUMMARY_REPORT_OPTIONS.find((item) => item.id === sourceId);
    if (!option) continue;

    const saved = await fetchSavedReportConfig(option.reportId);
    const processed = await previewProcessedDataset({
      reportId: option.reportId,
      configuration: saved?.configuration,
    });

    for (const row of processed.rows) {
      rows.push({
        ...row,
        _sourceReport: option.label,
      });
    }
  }

  return rows;
}

export function useSummaryGeneration() {
  const { completedReports, generatedSummary, setGeneratedSummary, markReportComplete } =
    useWorkflowSession();
  const { showToast } = useToast();

  const [selected, setSelected] = useState<ReportSourceId[]>([]);
  const [apiCompleted, setApiCompleted] = useState<Set<ReportSourceId>>(new Set());
  const [isGenerating, setIsGenerating] = useState(false);
  const [templates, setTemplates] = useState<PromptTemplateListItem[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [selectedSummaryType, setSelectedSummaryType] =
    useState<SummaryType>("executive");
  const [sectionResults, setSectionResults] = useState<
    Partial<Record<SummaryType, GeneratedSummaryResult>>
  >({});

  const effectiveCompleted = useMemo(
    () => new Set<ReportSourceId>([...completedReports, ...apiCompleted]),
    [apiCompleted, completedReports],
  );

  useEffect(() => {
    summaryApi
      .listTemplates({ is_enabled: true })
      .then((res) => setTemplates(res.templates))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchGeneratedReports()
      .then((response) => {
        const completed = new Set<ReportSourceId>();
        for (const report of response.reports) {
          const sourceId = REPORT_ID_TO_SOURCE[report.reportId as ReportId];
          if (sourceId) {
            completed.add(sourceId);
            markReportComplete(sourceId);
          }
        }
        setApiCompleted(completed);
      })
      .catch(() => {});
  }, [markReportComplete]);

  useEffect(() => {
    setSelected((current) => {
      const fromSession = SUMMARY_REPORT_OPTIONS.filter((option) =>
        effectiveCompleted.has(option.id),
      ).map((option) => option.id);
      const merged = new Set([
        ...current.filter((id) => effectiveCompleted.has(id)),
        ...fromSession,
      ]);
      return Array.from(merged);
    });
  }, [effectiveCompleted]);

  const toggleReport = useCallback(
    (id: ReportSourceId) => {
      if (!effectiveCompleted.has(id)) return;
      setSelected((current) =>
        current.includes(id)
          ? current.filter((item) => item !== id)
          : [...current, id],
      );
    },
    [effectiveCompleted],
  );

  const generateOne = useCallback(
    async (summaryType: SummaryType, dataset: Record<string, unknown>[], regenerate = false) => {
      const reportNames = selected
        .map((id) => SUMMARY_REPORT_OPTIONS.find((option) => option.id === id)?.label ?? id)
        .join(", ");

      const payload = {
        summary_type: summaryType,
        prompt_template_id: selectedTemplateId || undefined,
        dataset,
        metadata: {
          report_name: "Railway Intelligence Summary",
          report_period: new Date().toISOString().split("T")[0],
          included_reports: reportNames ? reportNames.split(", ") : [],
        },
        regenerate,
      };

      return summaryApi.generate(payload);
    },
    [selected, selectedTemplateId],
  );

  const handleGenerate = useCallback(async () => {
    if (selected.length === 0) {
      showToast("warning", "Select reports", "Choose at least one completed report.");
      return;
    }

    setIsGenerating(true);
    try {
      const dataset = await buildDatasetForReports(selected);
      if (dataset.length === 0) {
        showToast("warning", "No data", "Selected reports have no processed rows.");
        return;
      }

      const typesToGenerate = selectedTemplateId
        ? [selectedSummaryType]
        : SUMMARY_TYPES;

      const results: Partial<Record<SummaryType, GeneratedSummaryResult>> = {};

      for (const type of typesToGenerate) {
        const result = await generateOne(type, dataset);
        results[type] = result;
      }

      setSectionResults(results);
      const mapped = mapResultToSection(results);
      setGeneratedSummary(mapped);
      showToast("success", "Summary generated");
    } catch {
      showToast("error", "Generation failed", "Could not generate summary.");
    } finally {
      setIsGenerating(false);
    }
  }, [
    selected,
    selectedTemplateId,
    selectedSummaryType,
    generateOne,
    setGeneratedSummary,
    showToast,
  ]);

  const handleRegenerate = useCallback(
    async (summaryType: SummaryType) => {
      setIsGenerating(true);
      try {
        const dataset = await buildDatasetForReports(selected);
        const result = await generateOne(summaryType, dataset, true);
        setSectionResults((prev) => {
          const next = { ...prev, [summaryType]: result };
          setGeneratedSummary(mapResultToSection(next));
          return next;
        });
        showToast("success", "Regenerated", SUMMARY_TYPE_LABELS[summaryType]);
      } catch {
        showToast("error", "Regeneration failed");
      } finally {
        setIsGenerating(false);
      }
    },
    [generateOne, selected, setGeneratedSummary, showToast],
  );

  const handleReset = useCallback(() => {
    setSelected(Array.from(effectiveCompleted));
    setGeneratedSummary(null);
    setSectionResults({});
  }, [effectiveCompleted, setGeneratedSummary]);

  const handleCopy = useCallback(
    async (text: string) => {
      await navigator.clipboard.writeText(text);
      showToast("success", "Copied to clipboard");
    },
    [showToast],
  );

  const handleDownload = useCallback(
    (content: string, filename: string) => {
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast("success", "Download started");
    },
    [showToast],
  );

  const handleDownloadAll = useCallback(() => {
    if (!generatedSummary) return;
    const content = [
      "=== EXECUTIVE SUMMARY ===",
      generatedSummary.executive,
      "",
      "=== WHATSAPP SUMMARY ===",
      generatedSummary.whatsapp,
      "",
      "=== OFFICIAL EMAIL ===",
      generatedSummary.email,
      "",
      "=== DAILY HIGHLIGHTS ===",
      generatedSummary.dailyHighlights,
      "",
      "=== KEY OBSERVATIONS ===",
      generatedSummary.keyObservations,
    ].join("\n");
    handleDownload(content, "railway-summary.txt");
  }, [generatedSummary, handleDownload]);

  return {
    reportOptions: SUMMARY_REPORT_OPTIONS,
    selected,
    completedReports: effectiveCompleted,
    generatedSummary,
    sectionResults,
    isGenerating,
    templates,
    selectedTemplateId,
    setSelectedTemplateId,
    selectedSummaryType,
    setSelectedSummaryType,
    summaryTypes: SUMMARY_TYPES,
    summaryTypeLabels: SUMMARY_TYPE_LABELS,
    toggleReport,
    handleGenerate,
    handleRegenerate,
    handleReset,
    handleCopy,
    handleDownload,
    handleDownloadAll,
  };
}
