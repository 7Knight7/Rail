import { useRef, useState } from "react";
import {
  Bot,
  Download,
  FileSpreadsheet,
  Globe,
  Lock,
  RefreshCw,
  Save,
  Search,
  Settings2,
  Shield,
  Upload,
  Zap,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { usePermissions } from "@/hooks/usePermissions";
import { cn } from "@/utils/cn";
import { SettingField } from "@/features/settings/components/SettingField";
import { useAppSettings } from "@/features/settings/hooks/useAppSettings";
import { SETTINGS_CATEGORY_META } from "@/api/settings";

const CATEGORY_ICONS: Record<string, typeof Settings2> = {
  general: Settings2,
  report: FileSpreadsheet,
  upload: Upload,
  export: Download,
  summary: Bot,
  automation: Zap,
  security: Shield,
  system: Globe,
};

const CATEGORY_ORDER = [
  "general",
  "report",
  "upload",
  "export",
  "summary",
  "automation",
  "security",
  "system",
];

export function SettingsPage() {
  const { canManageSettings } = usePermissions();
  const [activeCategory, setActiveCategory] = useState<string>("general");
  const [searchQuery, setSearchQuery] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    categories,
    loading,
    saving,
    error,
    hasChanges,
    getValue,
    setValue,
    save,
    resetCategory,
    exportSettings,
    importSettings,
    reload,
  } = useAppSettings(
    searchQuery ? null : activeCategory,
    searchQuery || undefined,
  );

  const visibleCategories = searchQuery
    ? categories
    : categories.filter((c) => c.slug === activeCategory);

  const sidebarCategories = CATEGORY_ORDER.map((slug) => ({
    slug,
    ...SETTINGS_CATEGORY_META[slug],
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Settings"
          description="Centralized configuration for the entire platform"
          breadcrumbs={[{ label: "System" }, { label: "Settings" }]}
        />
        {canManageSettings && (
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={saving}
            >
              <Upload className="mr-2 h-4 w-4" />
              Import
            </Button>
            <Button variant="secondary" onClick={() => void exportSettings()} disabled={saving}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button
              variant="secondary"
              onClick={() => void resetCategory(activeCategory)}
              disabled={saving || !canManageSettings}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Reset
            </Button>
            <Button onClick={() => void save()} disabled={saving || !hasChanges}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void importSettings(file);
          e.target.value = "";
        }}
      />

      {!canManageSettings && (
        <Alert variant="info" title="Read-only access">
          You can view settings. Contact an administrator to make changes.
        </Alert>
      )}

      {error && (
        <Alert variant="error" title="Error">
          {error}{" "}
          <button type="button" className="underline" onClick={() => void reload()}>
            Retry
          </button>
        </Alert>
      )}

      <div className="flex flex-col gap-6 lg:flex-row">
        <aside className="w-full shrink-0 lg:w-64">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Categories</CardTitle>
            </CardHeader>
            <CardBody className="space-y-1 p-2">
              {sidebarCategories.map((cat) => {
                const Icon = CATEGORY_ICONS[cat.slug] ?? Settings2;
                const isActive = !searchQuery && activeCategory === cat.slug;
                return (
                  <button
                    key={cat.slug}
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      setActiveCategory(cat.slug);
                    }}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                      isActive
                        ? "bg-blue-50 font-medium text-blue-700"
                        : "text-slate-600 hover:bg-slate-50",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{cat.label}</span>
                  </button>
                );
              })}
            </CardBody>
          </Card>
        </aside>

        <div className="min-w-0 flex-1 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search settings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {loading ? (
            <div className="flex justify-center py-16">
              <Spinner size="lg" />
            </div>
          ) : visibleCategories.length === 0 ? (
            <Card>
              <CardBody className="py-12 text-center text-sm text-slate-500">
                No settings match your search.
              </CardBody>
            </Card>
          ) : (
            visibleCategories.map((category) => (
              <Card key={category.slug}>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    {(() => {
                      const Icon = CATEGORY_ICONS[category.slug] ?? Lock;
                      return <Icon className="h-5 w-5 text-slate-500" />;
                    })()}
                    <div>
                      <CardTitle>{category.label}</CardTitle>
                      {category.description && (
                        <CardDescription>{category.description}</CardDescription>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardBody>
                  <div className="grid gap-6 sm:grid-cols-2">
                    {category.settings.map((setting) => (
                      <div
                        key={setting.id}
                        className={cn(
                          setting.value_type === "json" && "sm:col-span-2",
                          setting.value_type === "multiselect" && "sm:col-span-2",
                        )}
                      >
                        <SettingField
                          setting={setting}
                          value={getValue(category.slug, setting.key)}
                          onChange={(value) => {
                            if (canManageSettings) {
                              setValue(category.slug, setting.key, value);
                            }
                          }}
                        />
                        {setting.is_modified && (
                          <p className="mt-1 text-xs text-amber-600">Modified from default</p>
                        )}
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
