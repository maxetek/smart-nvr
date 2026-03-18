import { useState } from "react";
import { Grid2x2, Grid3x3, Maximize2 } from "lucide-react";
import { useCameras } from "@/hooks/use-cameras";
import { CameraPlayer } from "@/components/cameras/CameraPlayer";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type GridSize = 1 | 4 | 9;

export default function LiveViewPage() {
  const { data: camerasData, isLoading } = useCameras({ limit: 100 });
  const cameras = camerasData?.items || [];
  const [gridSize, setGridSize] = useState<GridSize>(4);
  const [assignments, setAssignments] = useState<Record<number, string>>({});

  const gridCells = Array.from({ length: gridSize }, (_, i) => i);
  const gridCols =
    gridSize === 1
      ? "grid-cols-1"
      : gridSize === 4
        ? "grid-cols-1 md:grid-cols-2"
        : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3";

  const cameraOptions = cameras.map((c) => ({ value: c.name, label: c.name }));

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Live View</h1>
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="aspect-video" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-100">Live View</h1>
        <div className="flex items-center gap-2">
          <Button
            variant={gridSize === 1 ? "default" : "outline"}
            size="icon"
            onClick={() => setGridSize(1)}
            title="1x1"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
          <Button
            variant={gridSize === 4 ? "default" : "outline"}
            size="icon"
            onClick={() => setGridSize(4)}
            title="2x2"
          >
            <Grid2x2 className="h-4 w-4" />
          </Button>
          <Button
            variant={gridSize === 9 ? "default" : "outline"}
            size="icon"
            onClick={() => setGridSize(9)}
            title="3x3"
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className={cn("grid gap-3", gridCols)}>
        {gridCells.map((idx) => {
          const cameraName = assignments[idx];
          return (
            <div key={idx} className="space-y-2">
              <Select
                options={cameraOptions}
                value={cameraName || ""}
                onChange={(e) =>
                  setAssignments({ ...assignments, [idx]: e.target.value })
                }
                placeholder="Select camera..."
              />
              {cameraName ? (
                <div className="group">
                  <CameraPlayer cameraName={cameraName} />
                </div>
              ) : (
                <div className="flex aspect-video items-center justify-center rounded-md border border-gray-800 bg-gray-900">
                  <p className="text-sm text-gray-500">No camera selected</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
