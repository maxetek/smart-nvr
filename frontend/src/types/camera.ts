export interface Camera {
  id: string;
  name: string;
  is_enabled: boolean;
  location: string | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  created_at: string;
  updated_at: string;
}

export interface CameraDetail extends Camera {
  event_count: number;
  pattern_count: number;
}

export interface CameraCreate {
  name: string;
  rtsp_url: string;
  sub_stream_url?: string;
  location?: string;
  width?: number;
  height?: number;
  fps?: number;
}

export interface CameraUpdate {
  name?: string;
  rtsp_url?: string;
  sub_stream_url?: string;
  location?: string;
  is_enabled?: boolean;
  width?: number;
  height?: number;
  fps?: number;
}
