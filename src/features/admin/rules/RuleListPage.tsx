import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Copy,
  Edit,
  MoreVertical,
  Settings2,
  ToggleLeft,
  ToggleRight,
  Trash2,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { AdminListToolbar } from "@/components/admin/AdminListToolbar";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { DuplicateNameDialog } from "@/components/admin/DuplicateNameDialog";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { Select } from "@/components/ui/Select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/DropdownMenu";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/ui/Toast";
import { rulesApi, type RuleListItem } from "@/api/rules";

const CATEGORY_OPTIONS = [
  { value: "all", label: "All Categories" },
  { value: "column", label: "Column" },
  { value: "conditional", label: "Conditional" },
  { value: "sorting", label: "Sorting" },
  { value: "filter", label: "Filter" },
  { value: "top", label: "Top/Limit" },
  { value: "highlight", label: "Highlight" },
  { value: "calculation", label: "Calculation" },
  { value: "merge", label: "Merge" },
];

export function RuleListPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [rules, setRules] = useState<RuleListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "enabled" | "disabled">("all");

  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; rule: RuleListItem | null }>({
    open: false,
    rule: null,
  });
  const [duplicateDialog, setDuplicateDialog] = useState<{
    open: boolean;
    rule: RuleListItem | null;
    newName: string;
  }>({
    open: false,
    rule: null,
    newName: "",
  });
  const [acting, setActing] = useState(false);

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const params: { category?: string; is_enabled?: boolean } = {};
      if (categoryFilter !== "all") params.category = categoryFilter;
      if (statusFilter === "enabled") params.is_enabled = true;
      if (statusFilter === "disabled") params.is_enabled = false;

      const response = await rulesApi.list(params);
      setRules(response.rules);
    } catch {
      showToast("error", "Failed to load rules");
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, showToast, statusFilter]);

  useEffect(() => {
    void loadRules();
  }, [loadRules]);

  const filteredRules = useMemo(() => {
    if (!searchQuery) return rules;
    const query = searchQuery.toLowerCase();
    return rules.filter(
      (rule) =>
        rule.name.toLowerCase().includes(query) ||
        rule.description?.toLowerCase().includes(query) ||
        rule.rule_type.toLowerCase().includes(query),
    );
  }, [rules, searchQuery]);

  const handleToggle = async (rule: RuleListItem) => {
    try {
      await rulesApi.toggle(rule.id);
      showToast("success", `Rule ${rule.is_enabled ? "disabled" : "enabled"}`);
      await loadRules();
    } catch {
      showToast("error", "Failed to toggle rule");
    }
  };

  const handleDelete = async () => {
    if (!deleteDialog.rule) return;
    setActing(true);
    try {
      await rulesApi.delete(deleteDialog.rule.id);
      showToast("success", "Rule deleted");
      setDeleteDialog({ open: false, rule: null });
      await loadRules();
    } catch {
      showToast("error", "Failed to delete rule");
    } finally {
      setActing(false);
    }
  };

  const handleDuplicate = async () => {
    if (!duplicateDialog.rule || !duplicateDialog.newName.trim()) return;
    setActing(true);
    try {
      const created = await rulesApi.duplicate(
        duplicateDialog.rule.id,
        duplicateDialog.newName.trim(),
      );
      showToast("success", "Rule duplicated");
      setDuplicateDialog({ open: false, rule: null, newName: "" });
      navigate(`/admin/rules/${created.id}/edit`);
    } catch {
      showToast("error", "Failed to duplicate rule");
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Business Rules"
        description="Configure and manage data processing rules"
        breadcrumbs={[{ label: "Administration" }, { label: "Business Rules" }]}
      />

      <AdminListToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search rules..."
        createLabel="New Rule"
        onCreate={() => navigate("/admin/rules/new")}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        filterSlot={
          <Select
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
            className="w-44"
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        }
      />

      <Card>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : filteredRules.length === 0 ? (
            <EmptyState
              icon={Settings2}
              title="No rules found"
              description={
                searchQuery
                  ? "No rules match your search criteria"
                  : "Create your first business rule to get started"
              }
              action={
                !searchQuery ? (
                  <Button variant="primary" onClick={() => navigate("/admin/rules/new")}>
                    Create Rule
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-slate-500">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Category</th>
                    <th className="pb-3 font-medium">Type</th>
                    <th className="pb-3 font-medium">Priority</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRules.map((rule) => (
                    <tr key={rule.id} className="border-b last:border-0">
                      <td className="py-4">
                        <button
                          type="button"
                          className="font-medium text-slate-900 hover:text-primary"
                          onClick={() => navigate(`/admin/rules/${rule.id}/edit`)}
                        >
                          {rule.name}
                        </button>
                        {rule.description && (
                          <p className="line-clamp-1 text-slate-500">{rule.description}</p>
                        )}
                      </td>
                      <td className="py-4 capitalize text-slate-600">{rule.category}</td>
                      <td className="py-4 text-slate-600">{rule.rule_type}</td>
                      <td className="py-4 text-slate-600">{rule.priority}</td>
                      <td className="py-4">
                        <StatusBadge variant={rule.is_enabled ? "success" : "neutral"}>
                          {rule.is_enabled ? "Enabled" : "Disabled"}
                        </StatusBadge>
                      </td>
                      <td className="py-4 text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/admin/rules/${rule.id}/edit`)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() =>
                                setDuplicateDialog({
                                  open: true,
                                  rule,
                                  newName: `${rule.name} (Copy)`,
                                })
                              }
                            >
                              <Copy className="mr-2 h-4 w-4" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => void handleToggle(rule)}>
                              {rule.is_enabled ? (
                                <>
                                  <ToggleLeft className="mr-2 h-4 w-4" />
                                  Disable
                                </>
                              ) : (
                                <>
                                  <ToggleRight className="mr-2 h-4 w-4" />
                                  Enable
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => setDeleteDialog({ open: true, rule })}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, rule: null })}
        title="Delete Rule"
        description={
          <>
            Are you sure you want to delete &ldquo;{deleteDialog.rule?.name}&rdquo;? This action
            cannot be undone.
          </>
        }
        confirmLabel="Delete"
        onConfirm={() => void handleDelete()}
        destructive
      />

      <DuplicateNameDialog
        open={duplicateDialog.open}
        onOpenChange={(open) =>
          setDuplicateDialog({ open, rule: null, newName: "" })
        }
        sourceName={duplicateDialog.rule?.name}
        name={duplicateDialog.newName}
        onNameChange={(newName) => setDuplicateDialog((current) => ({ ...current, newName }))}
        onConfirm={() => void handleDuplicate()}
        title="Duplicate Rule"
      />
    </div>
  );
}
