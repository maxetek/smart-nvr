import { useState, type FormEvent } from "react";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import type { Pattern, PatternCreate, PatternUpdate } from "@/types/pattern";

interface PatternFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cameraId: string;
  pattern?: Pattern;
  onSubmit: (data: PatternCreate | (PatternUpdate & { id: string })) => void;
  loading?: boolean;
}

const patternTypes = [
  { value: "line_cross", label: "Line Cross" },
  { value: "zone_intrusion", label: "Zone Intrusion" },
  { value: "loitering", label: "Loitering" },
  { value: "smoking", label: "Smoking" },
  { value: "weapon", label: "Weapon" },
  { value: "crowd", label: "Crowd" },
];

export function PatternForm({
  open,
  onOpenChange,
  cameraId,
  pattern,
  onSubmit,
  loading,
}: PatternFormProps) {
  const [name, setName] = useState(pattern?.name || "");
  const [patternType, setPatternType] = useState(pattern?.pattern_type || "line_cross");
  const [configJson, setConfigJson] = useState(
    pattern ? JSON.stringify(pattern.config_json, null, 2) : "{}"
  );
  const [cooldown, setCooldown] = useState(String(pattern?.cooldown_seconds ?? 60));
  const [enabled, setEnabled] = useState(pattern?.is_enabled ?? true);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEdit = !!pattern;

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Name is required";
    try {
      JSON.parse(configJson);
    } catch {
      errs.configJson = "Invalid JSON";
    }
    if (!cooldown || isNaN(Number(cooldown)) || Number(cooldown) < 0)
      errs.cooldown = "Must be a positive number";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    if (isEdit) {
      onSubmit({
        id: pattern.id,
        name,
        config_json: JSON.parse(configJson),
        cooldown_seconds: Number(cooldown),
        is_enabled: enabled,
      });
    } else {
      onSubmit({
        camera_id: cameraId,
        name,
        pattern_type: patternType,
        config_json: JSON.parse(configJson),
        cooldown_seconds: Number(cooldown),
        is_enabled: enabled,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <DialogTitle>{isEdit ? "Edit Pattern" : "Add Pattern"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="pat-name"
          label="Pattern Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
          placeholder="e.g. Perimeter Line"
        />
        {!isEdit && (
          <Select
            id="pat-type"
            label="Pattern Type"
            options={patternTypes}
            value={patternType}
            onChange={(e) => setPatternType(e.target.value)}
          />
        )}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-300">
            Config (JSON)
          </label>
          <textarea
            className="flex min-h-[100px] w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
          />
          {errors.configJson && (
            <p className="text-xs text-red-400">{errors.configJson}</p>
          )}
        </div>
        <Input
          id="pat-cooldown"
          label="Cooldown (seconds)"
          type="number"
          value={cooldown}
          onChange={(e) => setCooldown(e.target.value)}
          error={errors.cooldown}
        />
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="rounded border-gray-600 bg-gray-800"
          />
          Enabled
        </label>
        <div className="flex justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            {isEdit ? "Update" : "Create"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
