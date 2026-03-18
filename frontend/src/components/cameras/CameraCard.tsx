import { Camera as CameraIcon, MapPin } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Camera } from "@/types/camera";

interface CameraCardProps {
  camera: Camera;
  onClick: () => void;
}

export function CameraCard({ camera, onClick }: CameraCardProps) {
  return (
    <Card
      className="cursor-pointer p-4 transition-colors hover:border-gray-700"
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-gray-800 p-2">
            <CameraIcon className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <p className="font-medium text-gray-100">{camera.name}</p>
            {camera.location && (
              <div className="mt-0.5 flex items-center gap-1 text-xs text-gray-400">
                <MapPin className="h-3 w-3" />
                {camera.location}
              </div>
            )}
          </div>
        </div>
        <Badge variant={camera.is_enabled ? "success" : "outline"}>
          {camera.is_enabled ? "Enabled" : "Disabled"}
        </Badge>
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
        {camera.fps && <span>{camera.fps} FPS</span>}
        {camera.width && camera.height && (
          <span>
            {camera.width}x{camera.height}
          </span>
        )}
      </div>
    </Card>
  );
}
