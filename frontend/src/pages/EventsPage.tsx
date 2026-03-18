import { useState } from "react";
import { useEvents, useAcknowledgeEvents } from "@/hooks/use-events";
import { useCameras } from "@/hooks/use-cameras";
import { EventFilters } from "@/components/events/EventFilters";
import { EventTable } from "@/components/events/EventTable";
import { EventDetailModal } from "@/components/events/EventDetailModal";
import { Pagination } from "@/components/ui/pagination";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import type { Event, EventListParams } from "@/types/event";

export default function EventsPage() {
  const [filters, setFilters] = useState<EventListParams>({
    limit: 20,
    offset: 0,
  });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailEvent, setDetailEvent] = useState<Event | null>(null);

  const { data: eventsData, isLoading } = useEvents(filters);
  const { data: camerasData } = useCameras({ limit: 100 });
  const acknowledgeMutation = useAcknowledgeEvents();

  const events = eventsData?.items || [];
  const cameras = camerasData?.items || [];

  const handleToggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const handleSelectAll = () => {
    if (selectedIds.size === events.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(events.map((e) => e.id)));
    }
  };

  const handleBatchAcknowledge = async () => {
    if (selectedIds.size === 0) return;
    try {
      await acknowledgeMutation.mutateAsync({
        event_ids: Array.from(selectedIds),
      });
      setSelectedIds(new Set());
      toast.success(`${selectedIds.size} event(s) acknowledged`);
    } catch {
      toast.error("Failed to acknowledge events");
    }
  };

  const handleSingleAcknowledge = async (id: string) => {
    try {
      await acknowledgeMutation.mutateAsync({ event_ids: [id] });
      setDetailEvent(null);
      toast.success("Event acknowledged");
    } catch {
      toast.error("Failed to acknowledge event");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Events</h1>
        <Skeleton className="h-10" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-100">Events</h1>
        {selectedIds.size > 0 && (
          <Button
            onClick={handleBatchAcknowledge}
            loading={acknowledgeMutation.isPending}
          >
            Acknowledge ({selectedIds.size})
          </Button>
        )}
      </div>

      <EventFilters
        cameras={cameras}
        filters={filters}
        onFilterChange={(f) => setFilters({ ...f, offset: 0 })}
      />

      <div className="rounded-lg border border-gray-800 bg-gray-900">
        <EventTable
          events={events}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onSelectAll={handleSelectAll}
          onRowClick={setDetailEvent}
        />
      </div>

      {eventsData && (
        <Pagination
          total={eventsData.total}
          limit={eventsData.limit}
          offset={eventsData.offset}
          onPageChange={(offset) => setFilters({ ...filters, offset })}
        />
      )}

      <EventDetailModal
        event={detailEvent}
        open={!!detailEvent}
        onOpenChange={(open) => !open && setDetailEvent(null)}
        onAcknowledge={handleSingleAcknowledge}
      />
    </div>
  );
}
