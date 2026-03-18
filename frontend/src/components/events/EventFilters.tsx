import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import type { Camera } from "@/types/camera";
import type { EventListParams } from "@/types/event";

interface EventFiltersProps {
  cameras: Camera[];
  filters: EventListParams;
  onFilterChange: (filters: EventListParams) => void;
}

const eventTypes = [
  { value: "", label: "All Types" },
  { value: "line_cross", label: "Line Cross" },
  { value: "zone_intrusion", label: "Zone Intrusion" },
  { value: "loitering", label: "Loitering" },
  { value: "smoking", label: "Smoking" },
  { value: "weapon", label: "Weapon" },
  { value: "crowd", label: "Crowd" },
];

const severities = [
  { value: "", label: "All Severities" },
  { value: "critical", label: "Critical" },
  { value: "warning", label: "Warning" },
  { value: "info", label: "Info" },
];

const acknowledgedOptions = [
  { value: "", label: "All" },
  { value: "false", label: "Unacknowledged" },
  { value: "true", label: "Acknowledged" },
];

export function EventFilters({ cameras, filters, onFilterChange }: EventFiltersProps) {
  const cameraOptions = [
    { value: "", label: "All Cameras" },
    ...cameras.map((c) => ({ value: c.id, label: c.name })),
  ];

  return (
    <div className="flex flex-wrap gap-3">
      <div className="w-48">
        <Select
          options={cameraOptions}
          value={filters.camera_id || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              camera_id: e.target.value || undefined,
            })
          }
          placeholder="All Cameras"
        />
      </div>
      <div className="w-40">
        <Select
          options={eventTypes}
          value={filters.event_type || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              event_type: e.target.value || undefined,
            })
          }
        />
      </div>
      <div className="w-40">
        <Select
          options={severities}
          value={filters.severity || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              severity: e.target.value || undefined,
            })
          }
        />
      </div>
      <div className="w-40">
        <Select
          options={acknowledgedOptions}
          value={
            filters.is_acknowledged === undefined
              ? ""
              : String(filters.is_acknowledged)
          }
          onChange={(e) =>
            onFilterChange({
              ...filters,
              is_acknowledged:
                e.target.value === ""
                  ? undefined
                  : e.target.value === "true",
            })
          }
        />
      </div>
      <div className="w-40">
        <Input
          type="date"
          value={filters.start_date?.split("T")[0] || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              start_date: e.target.value
                ? `${e.target.value}T00:00:00`
                : undefined,
            })
          }
          placeholder="Start date"
        />
      </div>
      <div className="w-40">
        <Input
          type="date"
          value={filters.end_date?.split("T")[0] || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              end_date: e.target.value
                ? `${e.target.value}T23:59:59`
                : undefined,
            })
          }
          placeholder="End date"
        />
      </div>
    </div>
  );
}
