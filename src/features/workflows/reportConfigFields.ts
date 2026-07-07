/** Shared advanced settings fields for report configuration pages */

export const COMMON_ADVANCED_FIELDS = [
  {
    id: "hiddenColumns",
    label: "Hidden Columns",
    type: "text" as const,
    value: "",
    placeholder: "e.g. internal_id, raw_score",
  },
  {
    id: "customFilters",
    label: "Custom Filters",
    type: "text" as const,
    value: "",
    placeholder: "e.g. status=open",
  },
  {
    id: "highlightRules",
    label: "Highlight Rules",
    type: "select" as const,
    value: "top_values",
    options: [
      { value: "top_values", label: "Highlight top values" },
      { value: "threshold", label: "Above threshold" },
      { value: "none", label: "None" },
    ],
  },
  {
    id: "exportFormat",
    label: "Export Format",
    type: "select" as const,
    value: "xlsx",
    options: [
      { value: "xlsx", label: "Excel (.xlsx)" },
      { value: "pdf", label: "PDF" },
      { value: "csv", label: "CSV" },
    ],
  },
];

export const EXPORT_FORMAT_FIELD = {
  id: "exportFormat",
  label: "Export Format",
  type: "select" as const,
  value: "xlsx",
  options: [
    { value: "xlsx", label: "Excel (.xlsx)" },
    { value: "pdf", label: "PDF" },
    { value: "csv", label: "CSV" },
  ],
};
