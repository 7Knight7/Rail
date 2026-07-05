import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Layers,
  Building2,
  TrainFront,
  Tags,
  Route,
  MapPin,
  FileText,
  Settings,
  ScrollText,
  Menu,
  X,
  Bot,
  Zap,
} from "lucide-react";
import { ProfileDropdown } from "@/components/ProfileDropdown";
import { Button } from "@/components/ui/Button";
import { cn } from "@/utils/cn";
import { usePermissions } from "@/hooks/usePermissions";

const SIDEBAR_WIDTH = 260;

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
  visible?: boolean;
}

const mainNavItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
];

const workflowNavItems: NavItem[] = [
  { id: "merging", label: "Merging", path: "/workflows/merging", icon: Layers },
  { id: "division", label: "Division (Top 25)", path: "/workflows/division", icon: Building2 },
  { id: "train-no", label: "Train No (Top 20)", path: "/workflows/train-no", icon: TrainFront },
  { id: "types", label: "Types (Top 10)", path: "/workflows/types", icon: Tags },
  { id: "scr-train", label: "SCR Train", path: "/workflows/scr-train", icon: Route },
  { id: "scr-station", label: "SCR Station", path: "/workflows/scr-station", icon: MapPin },
  { id: "summary", label: "Summary Generation", path: "/workflows/summary", icon: FileText },
];

const adminNavItems: NavItem[] = [
  { id: "templates", label: "Templates", path: "/admin/templates", icon: FileText },
  { id: "prompts", label: "AI Prompts", path: "/admin/prompts", icon: Bot },
  { id: "automation", label: "Automation", path: "/admin/automation", icon: Zap },
  { id: "settings", label: "Settings", path: "/settings", icon: Settings },
  { id: "logs", label: "Logs", path: "/logs", icon: ScrollText },
];

function useVisibleAdminNavItems(): NavItem[] {
  const { canManageTemplates, canManageSettings, canViewLogs, isAdmin } = usePermissions();

  const visibility: Record<string, boolean> = {
    templates: canManageTemplates,
    prompts: canManageTemplates,
    automation: isAdmin,
    settings: canManageSettings,
    logs: canViewLogs,
  };

  return adminNavItems.filter((item) => visibility[item.id] ?? false);
}

function NavItemComponent({
  item,
  index,
  showIndex,
  onNavigate,
}: {
  item: NavItem;
  index?: number;
  showIndex?: boolean;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.path}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex min-h-10 items-center gap-3 rounded-md px-3 py-2 text-sm",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
          isActive
            ? "bg-blue-50 font-medium text-blue-700"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
        )
      }
    >
      {showIndex && index !== undefined && (
        <span
          className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-slate-200 text-xs font-medium text-slate-600"
          aria-hidden="true"
        >
          {index + 1}
        </span>
      )}
      <Icon size={18} className="shrink-0" aria-hidden="true" />
      <span className="truncate">{item.label}</span>
    </NavLink>
  );
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const visibleAdminItems = useVisibleAdminNavItems();

  return (
    <nav aria-label="Main navigation" className="flex-1 overflow-y-auto px-3 py-4">
      <div className="mb-6">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Main
        </p>
        <ul className="space-y-1" role="list">
          {mainNavItems.map((item) => (
            <li key={item.id}>
              <NavItemComponent item={item} onNavigate={onNavigate} />
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-6">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Reports
        </p>
        <ul className="space-y-1" role="list">
          {workflowNavItems.map((item, index) => (
            <li key={item.id}>
              <NavItemComponent
                item={item}
                index={index}
                showIndex
                onNavigate={onNavigate}
              />
            </li>
          ))}
        </ul>
      </div>

      {visibleAdminItems.length > 0 && (
        <div>
          <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            System
          </p>
          <ul className="space-y-1" role="list">
            {visibleAdminItems.map((item) => (
              <li key={item.id}>
                <NavItemComponent item={item} onNavigate={onNavigate} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </nav>
  );
}

function SidebarHeader() {
  return (
    <div className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-200 px-4">
      <div
        className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white"
        aria-hidden="true"
      >
        <TrainFront size={20} />
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-slate-900">Railway Reports</p>
        <p className="text-xs text-slate-500">Intelligence Platform</p>
      </div>
    </div>
  );
}

function getPageTitle(pathname: string, adminItems: NavItem[]): string {
  const allItems = [...mainNavItems, ...workflowNavItems, ...adminItems];
  const item = allItems.find((i) => i.path === pathname);
  return item?.label ?? "Railway Reports";
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const visibleAdminItems = useVisibleAdminNavItems();
  const pageTitle = getPageTitle(location.pathname, visibleAdminItems);

  return (
    <div className="min-h-screen bg-white">
      <aside
        className="fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-slate-200 bg-white lg:flex"
        style={{ width: SIDEBAR_WIDTH }}
        aria-label="Main navigation"
      >
        <SidebarHeader />
        <SidebarNav />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
          <div
            className="fixed inset-0 bg-slate-900/50"
            aria-hidden="true"
            onClick={() => setMobileOpen(false)}
          />
          <aside
            className="fixed inset-y-0 left-0 flex w-72 flex-col bg-white shadow-xl"
            style={{ maxWidth: SIDEBAR_WIDTH + 20 }}
          >
            <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
                  <TrainFront size={20} />
                </div>
                <span className="text-sm font-semibold text-slate-900">Railway Reports</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                aria-label="Close navigation menu"
                onClick={() => setMobileOpen(false)}
              >
                <X size={20} />
              </Button>
            </div>
            <SidebarNav onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-[260px]">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-4 border-b border-slate-200 bg-white px-4 lg:px-6">
          <Button
            className="lg:hidden"
            variant="ghost"
            size="sm"
            aria-label="Open navigation menu"
            onClick={() => setMobileOpen(true)}
          >
            <Menu size={20} />
          </Button>
          <h1 className="flex-1 text-sm font-medium text-slate-700">{pageTitle}</h1>
          <ProfileDropdown />
        </header>

        <main className="p-4 lg:p-6" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
