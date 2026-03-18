import { useState } from "react";
import { Plus } from "lucide-react";
import { useCameras } from "@/hooks/use-cameras";
import {
  usePatterns,
  useCreatePattern,
  useUpdatePattern,
  useDeletePattern,
} from "@/hooks/use-patterns";
import { PatternList } from "@/components/patterns/PatternList";
import { PatternForm } from "@/components/patterns/PatternForm";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import type { Pattern, PatternCreate, PatternUpdate } from "@/types/pattern";

export default function PatternsPage() {
  const { data: camerasData, isLoading: camerasLoading } = useCameras({ limit: 100 });
  const cameras = camerasData?.items || [];

  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editPattern, setEditPattern] = useState<Pattern | undefined>();

  const { data: patternsData, isLoading: patternsLoading } = usePatterns(
    selectedCameraId ? { camera_id: selectedCameraId, limit: 100 } : undefined
  );
  const patterns = patternsData?.items || [];

  const createMutation = useCreatePattern();
  const updateMutation = useUpdatePattern();
  const deleteMutation = useDeletePattern();

  const cameraOptions = cameras.map((c) => ({ value: c.id, label: c.name }));

  const handleSubmit = async (formData: PatternCreate | (PatternUpdate & { id: string })) => {
    try {
      if ("id" in formData) {
        await updateMutation.mutateAsync(formData);
        toast.success("Pattern updated");
      } else {
        await createMutation.mutateAsync(formData);
        toast.success("Pattern created");
      }
      setFormOpen(false);
      setEditPattern(undefined);
    } catch {
      toast.error("Failed to save pattern");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
      toast.success("Pattern deleted");
    } catch {
      toast.error("Failed to delete pattern");
    }
  };

  const handleToggle = async (pattern: Pattern) => {
    try {
      await updateMutation.mutateAsync({
        id: pattern.id,
        is_enabled: !pattern.is_enabled,
      });
      toast.success(pattern.is_enabled ? "Pattern disabled" : "Pattern enabled");
    } catch {
      toast.error("Failed to update pattern");
    }
  };

  if (camerasLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Patterns</h1>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-100">Patterns</h1>
        {selectedCameraId && (
          <Button
            onClick={() => {
              setEditPattern(undefined);
              setFormOpen(true);
            }}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Pattern
          </Button>
        )}
      </div>

      <div className="w-64">
        <Select
          options={cameraOptions}
          value={selectedCameraId}
          onChange={(e) => setSelectedCameraId(e.target.value)}
          placeholder="Select a camera..."
          label="Camera"
        />
      </div>

      {!selectedCameraId && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
          <p className="text-gray-400">Select a camera to view its patterns.</p>
        </div>
      )}

      {selectedCameraId && patternsLoading && <Skeleton className="h-64" />}

      {selectedCameraId && !patternsLoading && (
        <PatternList
          patterns={patterns}
          onEdit={(p) => {
            setEditPattern(p);
            setFormOpen(true);
          }}
          onDelete={handleDelete}
          onToggle={handleToggle}
        />
      )}

      {selectedCameraId && (
        <PatternForm
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) setEditPattern(undefined);
          }}
          cameraId={selectedCameraId}
          pattern={editPattern}
          onSubmit={handleSubmit}
          loading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}
