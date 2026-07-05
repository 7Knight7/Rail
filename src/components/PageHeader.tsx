import { ChevronRight, Home } from "lucide-react";
import { Link } from "react-router-dom";

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: Breadcrumb[];
}

export function PageHeader({ title, description, breadcrumbs }: PageHeaderProps) {
  return (
    <div className="mb-6">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" className="mb-3">
          <ol className="flex items-center gap-1 text-sm">
            <li>
              <Link
                to="/dashboard"
                className="flex items-center text-slate-500 hover:text-slate-700"
              >
                <Home className="h-4 w-4" />
              </Link>
            </li>
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center gap-1">
                <ChevronRight className="h-4 w-4 text-slate-400" />
                {crumb.href ? (
                  <Link
                    to={crumb.href}
                    className="text-slate-500 hover:text-slate-700"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="font-medium text-slate-900">{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      {description && (
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      )}
    </div>
  );
}
