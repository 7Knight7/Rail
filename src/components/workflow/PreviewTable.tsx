import { Table, Eye } from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";

interface Column {
  key: string;
  header: string;
  width?: string;
}

interface PreviewTableProps {
  title?: string;
  description?: string;
  columns: Column[];
  data: Record<string, string | number>[];
  maxRows?: number;
  emptyMessage?: string;
}

export function PreviewTable({
  title = "Data Preview",
  description = "Preview of uploaded data",
  columns,
  data,
  maxRows = 10,
  emptyMessage = "No data to preview. Upload a file to get started.",
}: PreviewTableProps) {
  const displayData = data.slice(0, maxRows);
  const hasMore = data.length > maxRows;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-slate-500" />
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>
              {description}
              {data.length > 0 && (
                <span className="ml-2 text-slate-500">
                  ({displayData.length} of {data.length} rows)
                </span>
              )}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardBody>
        {data.length === 0 ? (
          <EmptyState
            icon={Table}
            title="No data available"
            description={emptyMessage}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  {columns.map((col) => (
                    <th
                      key={col.key}
                      className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
                      style={{ width: col.width }}
                    >
                      {col.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayData.map((row, rowIndex) => (
                  <tr key={rowIndex} className="hover:bg-slate-50">
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        className="whitespace-nowrap px-3 py-2 text-slate-700"
                      >
                        {row[col.key] ?? "-"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {hasMore && (
              <p className="mt-3 text-center text-xs text-slate-500">
                Showing first {maxRows} rows. {data.length - maxRows} more rows hidden.
              </p>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
