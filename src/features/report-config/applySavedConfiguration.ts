import type { ReportConfiguration } from "@/api/processing";
import type { ColumnMetadata, FilterCondition } from "./types";
import type { ReportSettingsField } from "./buildReportConfiguration";

const SETTING_FILTER_COLUMNS = new Set([
  "Registration Date",
  "Division",
  "Zone",
]);

function reverseMapOperator(operator: string): string {
  const mapping: Record<string, string> = {
    equals: "eq",
    lt: "before",
    gt: "after",
  };
  return mapping[operator] ?? operator;
}

function findColumnId(columns: ColumnMetadata[], fieldName: string): string {
  const match = columns.find(
    (column) =>
      column.fieldName === fieldName ||
      column.displayName === fieldName ||
      column.id === fieldName,
  );
  return match?.id ?? "";
}

export interface AppliedSavedConfiguration {
  settings: ReportSettingsField[];
  advancedSettings: ReportSettingsField[];
  filterConditions: FilterCondition[];
  visibleColumnIds: string[];
}

export function applySavedConfiguration(
  config: ReportConfiguration,
  columns: ColumnMetadata[],
  settings: ReportSettingsField[],
  advancedSettings: ReportSettingsField[],
): AppliedSavedConfiguration {
  const visibleFromOrder = (config.columnOrder ?? [])
    .map((fieldName) => findColumnId(columns, fieldName))
    .filter((columnId): columnId is string => Boolean(columnId));

  const visibleColumnIds =
    visibleFromOrder.length > 0
      ? visibleFromOrder
      : columns
          .filter((column) => !config.hiddenColumns?.includes(column.fieldName))
          .map((column) => column.id);

  const filterConditions: FilterCondition[] = (config.filters ?? [])
    .filter((filter) => !SETTING_FILTER_COLUMNS.has(filter.column))
    .map((filter, index) => ({
      id: `saved-filter-${index}`,
      columnId: findColumnId(columns, filter.column),
      operator: reverseMapOperator(filter.operator),
      value: String(filter.value ?? ""),
      valueTo: filter.valueTo !== undefined ? String(filter.valueTo) : undefined,
      logic: filter.logic ?? "AND",
    }))
    .filter((condition) => condition.columnId);

  const updatedSettings = settings.map((field) => {
    if (field.id === "topCount" && config.topN?.count) {
      return { ...field, value: config.topN.count };
    }
    return field;
  });

  return {
    settings: updatedSettings,
    advancedSettings,
    filterConditions,
    visibleColumnIds,
  };
}
