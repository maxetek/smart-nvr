import { Camera, Activity, Bell, AlertTriangle } from "lucide-react";
import { useDashboard } from "@/hooks/use-dashboard";
import { StatCard } from "@/components/dashboard/StatCard";
import { EventChart } from "@/components/dashboard/EventChart";
import { PipelineStatus } from "@/components/dashboard/PipelineStatus";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Cameras"
          value={data.total_cameras}
          icon={Camera}
          color="text-blue-400"
        />
        <StatCard
          title="Active Cameras"
          value={data.active_cameras}
          icon={Activity}
          color="text-green-400"
        />
        <StatCard
          title="Events Today"
          value={data.total_events_today}
          icon={Bell}
          color="text-amber-400"
        />
        <StatCard
          title="Unacknowledged"
          value={data.unacknowledged_events}
          icon={AlertTriangle}
          color="text-red-400"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <EventChart
          data={data.events_by_type}
          title="Events by Type"
          color="#3b82f6"
        />

        <Card>
          <CardHeader>
            <CardTitle>Events by Severity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(data.events_by_severity).map(([severity, count]) => {
                const variant =
                  severity === "critical"
                    ? "destructive"
                    : severity === "warning"
                      ? "warning"
                      : "default";
                return (
                  <div
                    key={severity}
                    className="flex items-center justify-between rounded-md border border-gray-800 px-4 py-2"
                  >
                    <Badge variant={variant as "destructive" | "warning" | "default"} className="capitalize">
                      {severity}
                    </Badge>
                    <span className="text-lg font-semibold text-gray-100">
                      {count}
                    </span>
                  </div>
                );
              })}
              {Object.keys(data.events_by_severity).length === 0 && (
                <p className="text-sm text-gray-400">No events today.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <PipelineStatus status={data.pipeline_status} />
    </div>
  );
}
