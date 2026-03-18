import { format } from "date-fns";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Event } from "@/types/event";

interface EventDetailModalProps {
  event: Event | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAcknowledge: (id: string) => void;
}

function severityVariant(severity: string) {
  switch (severity.toLowerCase()) {
    case "critical":
      return "destructive" as const;
    case "warning":
      return "warning" as const;
    default:
      return "default" as const;
  }
}

export function EventDetailModal({
  event,
  open,
  onOpenChange,
  onAcknowledge,
}: EventDetailModalProps) {
  if (!event) return null;

  const metadata = event.metadata_json || {};

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <DialogTitle className="capitalize">
          {event.event_type.replace(/_/g, " ")} Event
        </DialogTitle>
      </DialogHeader>

      <div className="space-y-4">
        {event.thumbnail_path && (
          <div className="overflow-hidden rounded-md border border-gray-800">
            <img
              src={event.thumbnail_path}
              alt="Event thumbnail"
              className="w-full object-cover"
            />
          </div>
        )}

        {event.clip_path && (
          <div className="overflow-hidden rounded-md border border-gray-800">
            <video
              src={event.clip_path}
              controls
              className="w-full"
            />
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-400">Camera</p>
            <p className="text-gray-100">{event.camera_name || "—"}</p>
          </div>
          <div>
            <p className="text-gray-400">Timestamp</p>
            <p className="text-gray-100">
              {format(new Date(event.created_at), "MMM d, yyyy HH:mm:ss")}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Severity</p>
            <Badge variant={severityVariant(event.severity)}>
              {event.severity}
            </Badge>
          </div>
          <div>
            <p className="text-gray-400">Confidence</p>
            <p className="text-gray-100">{(event.confidence * 100).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-gray-400">Status</p>
            <Badge variant={event.is_acknowledged ? "success" : "warning"}>
              {event.is_acknowledged ? "Acknowledged" : "Pending"}
            </Badge>
          </div>
          {event.acknowledged_at && (
            <div>
              <p className="text-gray-400">Acknowledged At</p>
              <p className="text-gray-100">
                {format(new Date(event.acknowledged_at), "MMM d, yyyy HH:mm:ss")}
              </p>
            </div>
          )}
        </div>

        {Object.keys(metadata).length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium text-gray-400">Metadata</p>
            <div className="rounded-md border border-gray-800 bg-gray-800/50 p-3">
              <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                {JSON.stringify(metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {!event.is_acknowledged && (
          <div className="flex justify-end pt-2">
            <Button onClick={() => onAcknowledge(event.id)}>
              Acknowledge
            </Button>
          </div>
        )}
      </div>
    </Dialog>
  );
}
