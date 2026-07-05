import { Settings2 } from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Label } from "@/components/ui/Label";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

interface SettingField {
  id: string;
  label: string;
  type: "text" | "number" | "select" | "date";
  value: string | number;
  options?: { value: string; label: string }[];
  placeholder?: string;
  disabled?: boolean;
}

interface SettingsCardProps {
  title?: string;
  description?: string;
  fields: SettingField[];
  onChange?: (id: string, value: string | number) => void;
  disabled?: boolean;
}

export function SettingsCard({
  title = "Settings",
  description = "Configure workflow parameters",
  fields,
  onChange,
  disabled = false,
}: SettingsCardProps) {
  const handleChange = (id: string, value: string | number) => {
    if (!disabled) {
      onChange?.(id, value);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-slate-500" />
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardBody>
        <div className="grid gap-4 sm:grid-cols-2">
          {fields.map((field) => (
            <div key={field.id} className="space-y-1.5">
              <Label htmlFor={field.id}>{field.label}</Label>
              {field.type === "select" && field.options ? (
                <Select
                  id={field.id}
                  value={String(field.value)}
                  onChange={(e) => handleChange(field.id, e.target.value)}
                  disabled={disabled || field.disabled}
                >
                  {field.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              ) : (
                <Input
                  id={field.id}
                  type={field.type}
                  value={String(field.value)}
                  placeholder={field.placeholder}
                  onChange={(e) =>
                    handleChange(
                      field.id,
                      field.type === "number" ? Number(e.target.value) : e.target.value,
                    )
                  }
                  disabled={disabled || field.disabled}
                />
              )}
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
