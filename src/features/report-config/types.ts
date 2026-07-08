export type ColumnDataType = "text" | "number" | "date" | "status" | "boolean";

export interface ColumnMetadata {
  id: string;
  fieldName: string;
  displayName: string;
  dataType: ColumnDataType;
  nullable: boolean;
  uniqueValues: Array<string | number | boolean | null>;
  uniqueValueCount: number;
  filterable: boolean;
  sortable: boolean;
}

export interface DatasetMetadata {
  reportId: string;
  sourceFilename: string;
  headerRow: number;
  rowCount: number;
  columns: ColumnMetadata[];
  parsedAt: string;
}

export type FilterLogic = "AND" | "OR";

export interface FilterCondition {
  id: string;
  columnId: string;
  operator: string;
  value: string;
  valueTo?: string;
  logic: FilterLogic;
}

export interface ReportFilterConfig {
  conditions: FilterCondition[];
  visibleColumnIds: string[];
}

export type ReportId =
  | "merging"
  | "division"
  | "train-no"
  | "types"
  | "scr-train"
  | "scr-station";
