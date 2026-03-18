export interface DashboardData {
  total_cameras: number;
  active_cameras: number;
  total_events_today: number;
  unacknowledged_events: number;
  events_by_type: Record<string, number>;
  events_by_severity: Record<string, number>;
  recent_events_count_1h: number;
  pipeline_status: Record<string, unknown> | null;
}
