export interface Event {
  id: string;
  camera_id: string;
  camera_name: string | null;
  event_type: string;
  severity: string;
  confidence: number;
  thumbnail_path: string | null;
  clip_path: string | null;
  metadata_json: Record<string, unknown> | null;
  is_acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string;
}

export interface EventListParams {
  camera_id?: string;
  event_type?: string;
  severity?: string;
  start_date?: string;
  end_date?: string;
  is_acknowledged?: boolean;
  limit?: number;
  offset?: number;
}

export interface AcknowledgeRequest {
  event_ids: string[];
}
