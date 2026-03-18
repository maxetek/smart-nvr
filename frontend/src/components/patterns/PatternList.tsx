import { Edit2, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Pattern } from "@/types/pattern";

interface PatternListProps {
  patterns: Pattern[];
  onEdit: (pattern: Pattern) => void;
  onDelete: (id: string) => void;
  onToggle: (pattern: Pattern) => void;
}

export function PatternList({ patterns, onEdit, onDelete, onToggle }: PatternListProps) {
  if (patterns.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-400">
        No patterns configured for this camera.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {patterns.map((pattern) => (
        <div
          key={pattern.id}
          className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-900 p-4"
        >
          <div>
            <div className="flex items-center gap-2">
              <p className="font-medium text-gray-100">{pattern.name}</p>
              <Badge variant={pattern.is_enabled ? "success" : "outline"}>
                {pattern.is_enabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
            <p className="mt-1 text-xs text-gray-400 capitalize">
              {pattern.pattern_type.replace(/_/g, " ")} · Cooldown: {pattern.cooldown_seconds}s
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggle(pattern)}
            >
              {pattern.is_enabled ? "Disable" : "Enable"}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onEdit(pattern)}
            >
              <Edit2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onDelete(pattern.id)}
            >
              <Trash2 className="h-4 w-4 text-red-400" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
