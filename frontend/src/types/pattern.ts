export interface Pattern {
  id: string;
  camera_id: string;
  name: string;
  pattern_type: string;
  is_enabled: boolean;
  config_json: Record<string, unknown>;
  cooldown_seconds: number;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatternCreate {
  camera_id: string;
  name: string;
  pattern_type: string;
  config_json: Record<string, unknown>;
  cooldown_seconds?: number;
  is_enabled?: boolean;
}

export interface PatternUpdate {
  name?: string;
  config_json?: Record<string, unknown>;
  cooldown_seconds?: number;
  is_enabled?: boolean;
}
