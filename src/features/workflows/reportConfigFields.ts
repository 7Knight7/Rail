/** Shared advanced settings fields for report configuration pages */

export const HIGHLIGHT_RULES_FIELD = {
  id: "highlightRules",
  label: "Highlight Rules",
  type: "select" as const,
  value: "top_values",
  options: [
    { value: "top_values", label: "Highlight top values" },
    { value: "threshold", label: "Above threshold" },
    { value: "none", label: "None" },
  ],
};

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

/** Fields still rendered in the advanced settings card (filters/columns are separate). */
export const COMMON_ADVANCED_FIELDS = [HIGHLIGHT_RULES_FIELD];
