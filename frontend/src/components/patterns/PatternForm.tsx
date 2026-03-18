import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ZoneEditor } from "@/components/patterns/ZoneEditor";
import type { Pattern, PatternCreate, PatternUpdate } from "@/types/pattern";

interface PatternFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cameraId: string;
  pattern?: Pattern;
  onSubmit: (data: PatternCreate | (PatternUpdate & { id: string })) => void;
  loading?: boolean;
  snapshotUrl?: string;
}

const patternTypes = [
  { value: "line_cross", label: "Line Cross" },
  { value: "zone_intrusion", label: "Zone Intrusion" },
  { value: "loitering", label: "Loitering" },
  { value: "smoking", label: "Smoking" },
  { value: "weapon", label: "Weapon" },
  { value: "crowd", label: "Crowd" },
];

const zonePatternTypes = ["zone_intrusion", "loitering", "crowd"];
const linePatternTypes = ["line_cross"];
const mlPatternTypes = ["smoking", "weapon"];

function getEditorMode(patternType: string): "polygon" | "line" | null {
  if (linePatternTypes.includes(patternType)) return "line";
  if (zonePatternTypes.includes(patternType)) return "polygon";
  if (mlPatternTypes.includes(patternType)) return "polygon"; // optional zone
  return null;
}

function extractZoneFromConfig(config: Record<string, unknown>): number[][] {
  const zone = config.zone as number[][] | undefined;
  return zone || [];
}

function extractLineFromConfig(config: Record<string, unknown>): number[][] {
  const line = config.line as Record<string, number> | undefined;
  if (!line) return [];
  return [
    [line.x1, line.y1],
    [line.x2, line.y2],
  ];
}

export function PatternForm({
  open,
  onOpenChange,
  cameraId,
  pattern,
  onSubmit,
  loading,
  snapshotUrl,
}: PatternFormProps) {
  const [name, setName] = useState(pattern?.name || "");
  const [patternType, setPatternType] = useState(pattern?.pattern_type || "line_cross");
  const [configJson, setConfigJson] = useState(
    pattern ? JSON.stringify(pattern.config_json, null, 2) : "{}"
  );
  const [cooldown, setCooldown] = useState(String(pattern?.cooldown_seconds ?? 60));
  const [confidenceThreshold, setConfidenceThreshold] = useState(
    String((pattern?.config_json?.confidence_threshold as number) ?? 0.5)
  );
  const [temporalThreshold, setTemporalThreshold] = useState(
    String((pattern?.config_json?.temporal_threshold as number) ?? 5)
  );
  const [enabled, setEnabled] = useState(pattern?.is_enabled ?? true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showRawJson, setShowRawJson] = useState(false);

  const isEdit = !!pattern;
  const editorMode = getEditorMode(patternType);
  const hasVisualEditor = editorMode !== null && snapshotUrl;

  // Get initial coordinates for the editor
  const getInitialCoords = useCallback((): number[][] => {
    try {
      const config = JSON.parse(configJson);
      if (linePatternTypes.includes(patternType)) {
        return extractLineFromConfig(config);
      }
      return extractZoneFromConfig(config);
    } catch {
      return [];
    }
  }, [configJson, patternType]);

  // Update configJson when visual editor coordinates change
  const handleCoordsChange = useCallback(
    (coords: number[][]) => {
      try {
        const config = JSON.parse(configJson);

        if (linePatternTypes.includes(patternType)) {
          if (coords.length >= 2) {
            config.line = {
              x1: coords[0][0],
              y1: coords[0][1],
              x2: coords[1][0],
              y2: coords[1][1],
            };
          } else {
            delete config.line;
          }
        } else {
          if (coords.length >= 3) {
            config.zone = coords;
          } else {
            delete config.zone;
          }
        }

        setConfigJson(JSON.stringify(config, null, 2));
      } catch {
        // If configJson is invalid, create a new config
        const config: Record<string, unknown> = {};
        if (linePatternTypes.includes(patternType) && coords.length >= 2) {
          config.line = {
            x1: coords[0][0],
            y1: coords[0][1],
            x2: coords[1][0],
            y2: coords[1][1],
          };
        } else if (coords.length >= 3) {
          config.zone = coords;
        }
        setConfigJson(JSON.stringify(config, null, 2));
      }
    },
    [configJson, patternType]
  );

  // Sync threshold fields into configJson
  useEffect(() => {
    try {
      const config = JSON.parse(configJson);
      let changed = false;
      const ct = parseFloat(confidenceThreshold);
      const tt = parseInt(temporalThreshold, 10);

      if (!isNaN(ct) && config.confidence_threshold !== ct) {
        config.confidence_threshold = ct;
        changed = true;
      }
      if (!isNaN(tt) && config.temporal_threshold !== tt) {
        config.temporal_threshold = tt;
        changed = true;
      }
      if (changed) {
        setConfigJson(JSON.stringify(config, null, 2));
      }
    } catch {
      // ignore
    }
  }, [confidenceThreshold, temporalThreshold]);

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

        {/* Visual Editor */}
        {hasVisualEditor && editorMode && (
          <ZoneEditor
            imageUrl={snapshotUrl}
            mode={editorMode}
            initialData={getInitialCoords()}
            onChange={handleCoordsChange}
          />
        )}

        {/* Confidence Threshold */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-300">
            Confidence Threshold: {confidenceThreshold}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(e.target.value)}
            className="w-full"
          />
        </div>

        {/* Temporal Threshold */}
        <Input
          id="pat-temporal"
          label="Temporal Threshold (frames)"
          type="number"
          value={temporalThreshold}
          onChange={(e) => setTemporalThreshold(e.target.value)}
        />

        <Input
          id="pat-cooldown"
          label="Cooldown (seconds)"
          type="number"
          value={cooldown}
          onChange={(e) => setCooldown(e.target.value)}
          error={errors.cooldown}
        />

        {/* Raw JSON toggle */}
        <div className="space-y-1">
          <button
            type="button"
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            {showRawJson ? "Hide" : "Show"} raw JSON config
          </button>
          {showRawJson && (
            <>
              <textarea
                className="flex min-h-[100px] w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={configJson}
                onChange={(e) => setConfigJson(e.target.value)}
              />
              {errors.configJson && (
                <p className="text-xs text-red-400">{errors.configJson}</p>
              )}
            </>
          )}
        </div>

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
