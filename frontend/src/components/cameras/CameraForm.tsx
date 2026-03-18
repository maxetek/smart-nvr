import { useState, type FormEvent } from "react";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { Camera, CameraCreate, CameraUpdate } from "@/types/camera";

interface CameraFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  camera?: Camera;
  onSubmit: (data: CameraCreate | (CameraUpdate & { id: string })) => void;
  loading?: boolean;
}

export function CameraForm({ open, onOpenChange, camera, onSubmit, loading }: CameraFormProps) {
  const [name, setName] = useState(camera?.name || "");
  const [rtspUrl, setRtspUrl] = useState("");
  const [subStreamUrl, setSubStreamUrl] = useState("");
  const [location, setLocation] = useState(camera?.location || "");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEdit = !!camera;

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Name is required";
    if (!isEdit && !rtspUrl.trim()) errs.rtspUrl = "RTSP URL is required";
    if (!isEdit && rtspUrl && !rtspUrl.startsWith("rtsp://"))
      errs.rtspUrl = "URL must start with rtsp://";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    if (isEdit) {
      const update: CameraUpdate & { id: string } = { id: camera.id };
      if (name !== camera.name) update.name = name;
      if (location !== (camera.location || "")) update.location = location || undefined;
      if (rtspUrl) update.rtsp_url = rtspUrl;
      if (subStreamUrl) update.sub_stream_url = subStreamUrl;
      onSubmit(update);
    } else {
      onSubmit({
        name,
        rtsp_url: rtspUrl,
        sub_stream_url: subStreamUrl || undefined,
        location: location || undefined,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <DialogTitle>{isEdit ? "Edit Camera" : "Add Camera"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="cam-name"
          label="Camera Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
          placeholder="e.g. Front Entrance"
        />
        <Input
          id="cam-rtsp"
          label="RTSP URL"
          value={rtspUrl}
          onChange={(e) => setRtspUrl(e.target.value)}
          error={errors.rtspUrl}
          placeholder="rtsp://192.168.1.100:554/stream"
        />
        <Input
          id="cam-sub"
          label="Sub-stream URL (optional)"
          value={subStreamUrl}
          onChange={(e) => setSubStreamUrl(e.target.value)}
          placeholder="rtsp://192.168.1.100:554/substream"
        />
        <Input
          id="cam-location"
          label="Location (optional)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. Building A, Floor 1"
        />
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
