import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PipelineStatusProps {
  status: Record<string, unknown> | null;
}

export function PipelineStatus({ status }: PipelineStatusProps) {
  if (!status) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-400">No pipeline data available.</p>
        </CardContent>
      </Card>
    );
  }

  const entries = Object.entries(status);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.map(([name, info]) => {
            const cameraInfo = info as Record<string, unknown>;
            const running = cameraInfo.running as boolean;
            const fps = cameraInfo.fps as number | undefined;
            return (
              <div
                key={name}
                className="flex items-center justify-between rounded-md border border-gray-800 px-4 py-2"
              >
                <span className="text-sm text-gray-100">{name}</span>
                <div className="flex items-center gap-3">
                  {fps !== undefined && (
                    <span className="text-xs text-gray-400">{fps} FPS</span>
                  )}
                  <Badge variant={running ? "success" : "destructive"}>
                    {running ? "Running" : "Stopped"}
                  </Badge>
                </div>
              </div>
            );
          })}
          {entries.length === 0 && (
            <p className="text-sm text-gray-400">No cameras in pipeline.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
