import { format } from "date-fns";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { Event } from "@/types/event";

interface EventTableProps {
  events: Event[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
  onRowClick: (event: Event) => void;
}

function severityVariant(severity: string) {
  switch (severity.toLowerCase()) {
    case "critical":
      return "destructive" as const;
    case "warning":
      return "warning" as const;
    case "info":
      return "default" as const;
    default:
      return "outline" as const;
  }
}

export function EventTable({
  events,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onRowClick,
}: EventTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-10">
            <input
              type="checkbox"
              className="rounded border-gray-600 bg-gray-800"
              checked={events.length > 0 && selectedIds.size === events.length}
              onChange={onSelectAll}
            />
          </TableHead>
          <TableHead>Time</TableHead>
          <TableHead>Camera</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Severity</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {events.map((event) => (
          <TableRow
            key={event.id}
            className="cursor-pointer"
            onClick={() => onRowClick(event)}
          >
            <TableCell onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                className="rounded border-gray-600 bg-gray-800"
                checked={selectedIds.has(event.id)}
                onChange={() => onToggleSelect(event.id)}
              />
            </TableCell>
            <TableCell className="text-gray-300">
              {format(new Date(event.created_at), "MMM d, HH:mm:ss")}
            </TableCell>
            <TableCell>{event.camera_name || "—"}</TableCell>
            <TableCell className="capitalize">
              {event.event_type.replace(/_/g, " ")}
            </TableCell>
            <TableCell>
              <Badge variant={severityVariant(event.severity)}>
                {event.severity}
              </Badge>
            </TableCell>
            <TableCell>{(event.confidence * 100).toFixed(0)}%</TableCell>
            <TableCell>
              <Badge variant={event.is_acknowledged ? "success" : "warning"}>
                {event.is_acknowledged ? "Acked" : "Pending"}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
        {events.length === 0 && (
          <TableRow>
            <TableCell colSpan={7} className="text-center text-gray-400 py-8">
              No events found.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
