import { Plus, Trash2 } from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";

type FilterOperator =
  | "equals"
  | "not_equals"
  | "contains"
  | "gt"
  | "lt"
  | "gte"
  | "lte"
  | "in"
  | "not_in"
  | "is_null"
  | "is_not_null";

interface FilteringRule {
  column_name: string;
  operator: FilterOperator;
  value: string | null;
  value_type: "string" | "number" | "date" | "boolean";
  logic_group: "AND" | "OR";
}

interface FilteringRulesSectionProps {
  data: FilteringRule[];
  columns: string[];
  onChange: (data: FilteringRule[]) => void;
}

const operators = [
  { value: "equals", label: "Equals" },
  { value: "not_equals", label: "Not Equals" },
  { value: "contains", label: "Contains" },
  { value: "gt", label: "Greater Than" },
  { value: "lt", label: "Less Than" },
  { value: "gte", label: "Greater or Equal" },
  { value: "lte", label: "Less or Equal" },
  { value: "in", label: "In List" },
  { value: "not_in", label: "Not In List" },
  { value: "is_null", label: "Is Empty" },
  { value: "is_not_null", label: "Is Not Empty" },
];

export function FilteringRulesSection({ data, columns, onChange }: FilteringRulesSectionProps) {
  const addRule = () => {
    onChange([
      ...data,
      {
        column_name: columns[0] || "",
        operator: "equals" as FilterOperator,
        value: "",
        value_type: "string",
        logic_group: "AND",
      },
    ]);
  };

  const updateRule = (index: number, updates: Partial<FilteringRule>) => {
    onChange(data.map((r, i) => (i === index ? { ...r, ...updates } : r)));
  };

  const removeRule = (index: number) => {
    onChange(data.filter((_, i) => i !== index));
  };

  const needsValue = (operator: string) => !["is_null", "is_not_null"].includes(operator);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Filtering Rules</CardTitle>
            <CardDescription>Define conditions to filter output rows</CardDescription>
          </div>
          <Button variant="secondary" onClick={addRule} disabled={columns.length === 0}>
            <Plus className="mr-2 h-4 w-4" />
            Add Rule
          </Button>
        </div>
      </CardHeader>
      <CardBody>
        {columns.length === 0 ? (
          <EmptyState
            title="No columns available"
            description="Add column mappings first to configure filtering rules."
          />
        ) : data.length === 0 ? (
          <EmptyState
            title="No filtering rules"
            description="Add filtering rules to include/exclude specific rows."
            action={
              <Button variant="primary" onClick={addRule}>
                <Plus className="mr-2 h-4 w-4" />
                Add Rule
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {data.map((rule, index) => (
              <div
                key={index}
                className="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-start gap-4">
                  {index > 0 && (
                    <Select
                      value={rule.logic_group}
                      onChange={(e) =>
                        updateRule(index, { logic_group: e.target.value as "AND" | "OR" })
                      }
                      className="w-20"
                    >
                      <option value="AND">AND</option>
                      <option value="OR">OR</option>
                    </Select>
                  )}

                  <div className="flex-1 grid gap-3 sm:grid-cols-4">
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-slate-500">Column</label>
                      <Select
                        value={rule.column_name}
                        onChange={(e) => updateRule(index, { column_name: e.target.value })}
                      >
                        {columns.map((col) => (
                          <option key={col} value={col}>
                            {col}
                          </option>
                        ))}
                      </Select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-medium text-slate-500">Operator</label>
                      <Select
                        value={rule.operator}
                        onChange={(e) => updateRule(index, { operator: e.target.value as FilterOperator })}
                      >
                        {operators.map((op) => (
                          <option key={op.value} value={op.value}>
                            {op.label}
                          </option>
                        ))}
                      </Select>
                    </div>

                    {needsValue(rule.operator) && (
                      <>
                        <div className="space-y-1">
                          <label className="text-xs font-medium text-slate-500">Value</label>
                          <Input
                            value={rule.value || ""}
                            onChange={(e) => updateRule(index, { value: e.target.value })}
                            placeholder="Enter value"
                          />
                        </div>

                        <div className="space-y-1">
                          <label className="text-xs font-medium text-slate-500">Value Type</label>
                          <Select
                            value={rule.value_type}
                            onChange={(e) =>
                              updateRule(index, {
                                value_type: e.target.value as FilteringRule["value_type"],
                              })
                            }
                          >
                            <option value="string">Text</option>
                            <option value="number">Number</option>
                            <option value="date">Date</option>
                            <option value="boolean">Boolean</option>
                          </Select>
                        </div>
                      </>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeRule(index)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
