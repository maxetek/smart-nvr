import { useState } from "react";
import { Plus } from "lucide-react";
import { useCameras, useCreateCamera, useUpdateCamera, useDeleteCamera } from "@/hooks/use-cameras";
import { useAuthStore } from "@/stores/auth-store";
import { CameraCard } from "@/components/cameras/CameraCard";
import { CameraForm } from "@/components/cameras/CameraForm";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import type { Camera, CameraCreate, CameraUpdate } from "@/types/camera";

export default function CamerasPage() {
  const { data, isLoading } = useCameras({ limit: 100 });
  const user = useAuthStore((s) => s.user);
  const createMutation = useCreateCamera();
  const updateMutation = useUpdateCamera();
  const deleteMutation = useDeleteCamera();

  const [formOpen, setFormOpen] = useState(false);
  const [editCamera, setEditCamera] = useState<Camera | undefined>();
  const [deleteConfirm, setDeleteConfirm] = useState<Camera | null>(null);

  const cameras = data?.items || [];

  const handleSubmit = async (formData: CameraCreate | (CameraUpdate & { id: string })) => {
    try {
      if ("id" in formData) {
        await updateMutation.mutateAsync(formData);
        toast.success("Camera updated");
      } else {
        await createMutation.mutateAsync(formData);
        toast.success("Camera created");
      }
      setFormOpen(false);
      setEditCamera(undefined);
    } catch {
      toast.error("Failed to save camera");
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await deleteMutation.mutateAsync(deleteConfirm.id);
      toast.success("Camera deleted");
      setDeleteConfirm(null);
    } catch {
      toast.error("Failed to delete camera");
    }
  };

  const handleCardClick = (camera: Camera) => {
    setEditCamera(camera);
    setFormOpen(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Cameras</h1>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-100">Cameras</h1>
        <Button onClick={() => { setEditCamera(undefined); setFormOpen(true); }}>
          <Plus className="mr-2 h-4 w-4" />
          Add Camera
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cameras.map((camera) => (
          <div key={camera.id} className="relative">
            <CameraCard camera={camera} onClick={() => handleCardClick(camera)} />
            {user?.role === "admin" && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-2 top-2 text-red-400 hover:text-red-300"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteConfirm(camera);
                }}
              >
                Delete
              </Button>
            )}
          </div>
        ))}
      </div>

      {cameras.length === 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
          <p className="text-gray-400">No cameras configured yet.</p>
        </div>
      )}

      <CameraForm
        open={formOpen}
        onOpenChange={(open) => {
          setFormOpen(open);
          if (!open) setEditCamera(undefined);
        }}
        camera={editCamera}
        onSubmit={handleSubmit}
        loading={createMutation.isPending || updateMutation.isPending}
      />

      <Dialog
        open={!!deleteConfirm}
        onOpenChange={(open) => !open && setDeleteConfirm(null)}
      >
        <DialogHeader>
          <DialogTitle>Delete Camera</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{deleteConfirm?.name}"? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-3 pt-4">
          <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            loading={deleteMutation.isPending}
          >
            Delete
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
