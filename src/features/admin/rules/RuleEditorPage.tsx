import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Textarea } from "@/components/ui/Textarea";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";
import {
  rulesApi,
  RULE_TYPES_BY_CATEGORY,
  type CreateRuleRequest,
  type RuleCategory,
} from "@/api/rules";

const CATEGORIES: { value: RuleCategory; label: string }[] = [
  { value: "column", label: "Column Rules" },
  { value: "conditional", label: "Conditional Rules" },
  { value: "sorting", label: "Sorting Rules" },
  { value: "filter", label: "Filter Rules" },
  { value: "top", label: "Top/Limit Rules" },
  { value: "highlight", label: "Highlight Rules" },
  { value: "calculation", label: "Calculation Rules" },
  { value: "merge", label: "Merge Rules" },
];

interface FormState {
  name: string;
  description: string;
  templateId: string;
  category: RuleCategory;
  ruleType: string;
  configJson: string;
  priority: number;
  groupId: string;
  isEnabled: boolean;
  isGlobal: boolean;
}

const defaultFormState: FormState = {
  name: "",
  description: "",
  templateId: "",
  category: "column",
  ruleType: "rename",
  configJson: "{}",
  priority: 0,
  groupId: "",
  isEnabled: true,
  isGlobal: false,
};

export function RuleEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const isNew = !id || id === "new";

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(defaultFormState);

  useEffect(() => {
    if (isNew || !id) return;

    let cancelled = false;
    setLoading(true);
    rulesApi
      .get(id)
      .then((rule) => {
        if (cancelled) return;
        setForm({
          name: rule.name,
          description: rule.description ?? "",
          templateId: rule.template_id ?? "",
          category: rule.category,
          ruleType: rule.rule_type,
          configJson: JSON.stringify(rule.config, null, 2),
          priority: rule.priority,
          groupId: rule.group_id ?? "",
          isEnabled: rule.is_enabled,
          isGlobal: rule.is_global,
        });
      })
      .catch(() => {
        showToast("error", "Failed to load rule");
        navigate("/admin/rules");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id, isNew, navigate, showToast]);

  const ruleTypes = RULE_TYPES_BY_CATEGORY[form.category] ?? [];

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSave() {
    if (!form.name.trim()) {
      showToast("error", "Rule name is required");
      return;
    }

    let config: Record<string, unknown>;
    try {
      config = JSON.parse(form.configJson) as Record<string, unknown>;
    } catch {
      showToast("error", "Invalid JSON configuration");
      return;
    }

    const payload: CreateRuleRequest = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      template_id: form.templateId.trim() || undefined,
      category: form.category,
      rule_type: form.ruleType,
      config,
      priority: form.priority,
      group_id: form.groupId.trim() || undefined,
      is_enabled: form.isEnabled,
      is_global: form.isGlobal,
    };

    setSaving(true);
    try {
      if (isNew) {
        await rulesApi.create(payload);
        showToast("success", "Rule created");
      } else {
        await rulesApi.update(id!, payload);
        showToast("success", "Rule updated");
      }
      navigate("/admin/rules");
    } catch {
      showToast("error", `Failed to ${isNew ? "create" : "update"} rule`);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isNew ? "Create Rule" : "Edit Rule"}
        description={isNew ? "Create a new business rule" : `Editing: ${form.name}`}
        breadcrumbs={[
          { label: "Administration" },
          { label: "Business Rules", href: "/admin/rules" },
          { label: isNew ? "Create" : "Edit" },
        ]}
      />

      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={() => navigate("/admin/rules")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button variant="primary" onClick={() => void handleSave()} disabled={saving}>
          <Save className="mr-2 h-4 w-4" />
          {saving ? "Saving..." : "Save"}
        </Button>
      </div>

      <Card>
        <CardBody className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(event) => updateForm("name", event.target.value)}
                placeholder="Enter rule name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Input
                id="priority"
                type="number"
                min={0}
                value={form.priority}
                onChange={(event) => updateForm("priority", Number(event.target.value) || 0)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={form.description}
              onChange={(event) => updateForm("description", event.target.value)}
              rows={3}
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                id="category"
                value={form.category}
                onChange={(event) => {
                  const category = event.target.value as RuleCategory;
                  const types = RULE_TYPES_BY_CATEGORY[category];
                  updateForm("category", category);
                  updateForm("ruleType", types[0]?.value ?? "");
                  updateForm("configJson", "{}");
                }}
              >
                {CATEGORIES.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="ruleType">Rule Type</Label>
              <Select
                id="ruleType"
                value={form.ruleType}
                onChange={(event) => {
                  updateForm("ruleType", event.target.value);
                  updateForm("configJson", "{}");
                }}
              >
                {ruleTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="groupId">Group ID</Label>
              <Input
                id="groupId"
                value={form.groupId}
                onChange={(event) => updateForm("groupId", event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="templateId">Template ID</Label>
              <Input
                id="templateId"
                value={form.templateId}
                onChange={(event) => updateForm("templateId", event.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.isEnabled}
                onChange={(event) => updateForm("isEnabled", event.target.checked)}
              />
              Enabled
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.isGlobal}
                onChange={(event) => updateForm("isGlobal", event.target.checked)}
              />
              Global rule
            </label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="configJson">Configuration (JSON)</Label>
            <Textarea
              id="configJson"
              value={form.configJson}
              onChange={(event) => updateForm("configJson", event.target.value)}
              rows={12}
              className="font-mono text-xs"
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
