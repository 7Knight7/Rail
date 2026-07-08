import type { ColumnMetadata, FilterCondition, ReportId } from "./types";

export interface ReportSettingsField {
  id: string;
  value: string | number;
}

export interface FilterConditionConfig {
  column: string;
  operator: string;
  value: unknown;
  valueTo?: unknown;
  logic: "AND" | "OR";
}

export interface SortingConfig {
  column: string;
  direction: "asc" | "desc";
  priority: number;
}

export interface TopNConfig {
  enabled: boolean;
  mode: "top" | "bottom";
  count: number;
  byColumn: string;
}

export interface HighlightConfig {
  column: string;
  scope: "row";
  operator: string;
  value: unknown;
  backgroundColor: string;
}

export interface ReportConfigurationPayload {
  filters: FilterConditionConfig[];
  sorting: SortingConfig[];
  topN?: TopNConfig;
  hiddenColumns: string[];
  columnOrder: string[];
  highlights: HighlightConfig[];
}

export interface BuildReportConfigurationInput {
  reportId: ReportId;
  settings: ReportSettingsField[];
  advancedSettings: ReportSettingsField[];
  filterConditions: FilterCondition[];
  visibleColumnIds: string[];
  columns: ColumnMetadata[];
}

export interface ExportOptions {
  includeExcel: boolean;
  includePdf: boolean;
  includeCsv?: boolean;
  includeDashboard: boolean;
}

const DEFAULT_TOP_N_MODE: Partial<Record<ReportId, "top" | "bottom">> = {
  division: "bottom",
};

const SORT_COLUMN_CANDIDATES: Record<string, string[]> = {
  count: ["Complaints", "Registration Date"],
  complaints: ["Complaints"],
  division: ["Division"],
  train: ["Train No"],
  trainNo: ["Train No"],
  category: ["Category", "Complaint Type"],
  cause: ["Complaint Type", "Category"],
  station: ["Station"],
  zone: ["Zone"],
  percentage: ["Complaints"],
  received: ["Registration Date"],
};

const SETTING_FILTER_MAP: Record<
  string,
  { column: string; operator: string; skipValues?: string[] }
> = {
  reportDate: { column: "Registration Date", operator: "on" },
  division: { column: "Division", operator: "equals", skipValues: ["all"] },
  zone: { column: "Zone", operator: "equals", skipValues: ["all"] },
};

function getSettingValue(settings: ReportSettingsField[], id: string): string | number | undefined {
  return settings.find((field) => field.id === id)?.value;
}

function resolveColumnName(identifier: string, columns: ColumnMetadata[]): string {
  const candidates = SORT_COLUMN_CANDIDATES[identifier] ?? [identifier];
  for (const candidate of candidates) {
    const match = columns.find(
      (column) =>
        column.fieldName === candidate ||
        column.displayName === candidate ||
        column.id === candidate ||
        column.fieldName.toLowerCase() === candidate.toLowerCase(),
    );
    if (match) {
      return match.fieldName;
    }
  }
  return identifier;
}

function mapOperator(operator: string): string {
  const mapping: Record<string, string> = {
    eq: "equals",
    on: "equals",
    before: "lt",
    after: "gt",
  };
  return mapping[operator] ?? operator;
}

function mapFilterValue(operator: string, value: string, valueTo?: string): { value: unknown; valueTo?: unknown } {
  if (operator === "true") {
    return { value: true };
  }
  if (operator === "false") {
    return { value: false };
  }
  if (operator === "between") {
    const numeric = Number(value);
    const numericTo = Number(valueTo);
    return {
      value: Number.isNaN(numeric) ? value : numeric,
      valueTo: Number.isNaN(numericTo) ? valueTo : numericTo,
    };
  }
  const numeric = Number(value);
  if (!Number.isNaN(numeric) && ["eq", "gt", "lt", "gte", "lte"].includes(operator)) {
    return { value: numeric };
  }
  return { value };
}

function inferSortDirection(sortBy: string): "asc" | "desc" {
  if (["division", "train", "station", "category", "zone", "cause"].includes(sortBy)) {
    return "asc";
  }
  return "desc";
}

function buildFilters(
  filterConditions: FilterCondition[],
  settings: ReportSettingsField[],
  columns: ColumnMetadata[],
): FilterConditionConfig[] {
  const filters: FilterConditionConfig[] = [];

  for (const condition of filterConditions) {
    if (!condition.columnId) continue;
    const column = columns.find((item) => item.id === condition.columnId);
    if (!column) continue;

    const mappedOperator = mapOperator(condition.operator);
    const requiresValue = !["true", "false"].includes(condition.operator);
    if (requiresValue && !condition.value && condition.operator !== "between") {
      continue;
    }

    const mappedValue = mapFilterValue(condition.operator, condition.value, condition.valueTo);
    filters.push({
      column: column.fieldName,
      operator: mappedOperator,
      value: mappedValue.value,
      valueTo: mappedValue.valueTo,
      logic: condition.logic,
    });
  }

  for (const [settingId, rule] of Object.entries(SETTING_FILTER_MAP)) {
    const rawValue = getSettingValue(settings, settingId);
    if (rawValue === undefined || rawValue === "") continue;
    if (rule.skipValues?.includes(String(rawValue))) continue;

    const column = resolveColumnName(rule.column, columns);
    let value: unknown = rawValue;
    if (settingId === "zone") {
      value = String(rawValue).toUpperCase() === "SCR" ? "SCR" : rawValue;
    }
    if (settingId === "division") {
      value = String(rawValue)
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
    }

    filters.push({
      column,
      operator: mapOperator(rule.operator),
      value,
      logic: "AND",
    });
  }

  return filters;
}

function buildHighlights(
  advancedSettings: ReportSettingsField[],
  sortColumn: string,
): HighlightConfig[] {
  const highlightRules = String(
    advancedSettings.find((field) => field.id === "highlightRules")?.value ?? "none",
  );

  if (highlightRules === "none" || !sortColumn) {
    return [];
  }

  if (highlightRules === "threshold") {
    return [
      {
        column: sortColumn,
        scope: "row",
        operator: "gt",
        value: 100,
        backgroundColor: "#FFF4CC",
      },
    ];
  }

  return [
    {
      column: sortColumn,
      scope: "row",
      operator: "gt",
      value: 0,
      backgroundColor: "#FEF3C7",
    },
  ];
}

export function buildReportConfiguration(
  input: BuildReportConfigurationInput,
): ReportConfigurationPayload {
  const { settings, advancedSettings, filterConditions, visibleColumnIds, columns } = input;

  const sortBy = String(getSettingValue(settings, "sortBy") ?? "count");
  const sortColumn = resolveColumnName(sortBy, columns);
  const sorting: SortingConfig[] = [
    {
      column: sortColumn,
      direction: inferSortDirection(sortBy),
      priority: 1,
    },
  ];

  const topCount = Number(getSettingValue(settings, "topCount"));
  const topN: TopNConfig | undefined =
    Number.isFinite(topCount) && topCount > 0
      ? {
          enabled: true,
          mode: DEFAULT_TOP_N_MODE[input.reportId] ?? "top",
          count: topCount,
          byColumn: sortColumn,
        }
      : undefined;

  const visibleColumns = visibleColumnIds
    .map((columnId) => columns.find((column) => column.id === columnId)?.fieldName)
    .filter((columnName): columnName is string => Boolean(columnName));

  const hiddenColumns = columns
    .map((column) => column.fieldName)
    .filter((fieldName) => !visibleColumns.includes(fieldName));

  return {
    filters: buildFilters(filterConditions, settings, columns),
    sorting,
    topN,
    hiddenColumns,
    columnOrder: visibleColumns,
    highlights: buildHighlights(advancedSettings, sortColumn),
  };
}

export function getExportOptions(settings: ReportSettingsField[]): ExportOptions {
  const format = String(getSettingValue(settings, "exportFormat") ?? "xlsx");

  if (format === "pdf") {
    return { includeExcel: false, includePdf: true, includeDashboard: true };
  }
  if (format === "csv") {
    return { includeExcel: false, includePdf: false, includeCsv: true, includeDashboard: true };
  }

  return { includeExcel: true, includePdf: true, includeDashboard: true };
}

export function buildPreviewColumns(
  processedColumns: { name: string }[] | undefined,
  fallback: { key: string; header: string; width?: string }[],
) {
  if (!processedColumns?.length) {
    return fallback;
  }

  return processedColumns.map((column) => ({
    key: column.name,
    header: column.name,
  }));
}
