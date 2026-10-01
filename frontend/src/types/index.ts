export interface Camera {
  camera_id: string;
  name: string;
  latitude: number;
  longitude: number;
  intersection: string;
  direction: string;
  road_segment: string;
  speed_limit_kmh: number;
  fps: number;
  resolution: string;
  status: string;
  metrics?: CameraMetrics;
}

export interface CameraMetrics {
  camera_id: string;
  camera_name: string;
  intersection: string;
  vehicle_count_current: number;
  flow_rate_vph: number;
  density_veh_per_km: number;
  average_speed_kmh: number;
  speed_limit_kmh: number;
  level_of_service: string;
  congestion_status: string;
  status_color: string;
  class_distribution: Record<string, number>;
}

export interface Observation {
  id: number;
  camera_id: string;
  camera_name?: string;
  intersection?: string;
  timestamp: string;
  frame_id: number;
  track_id: number;
  bbox_x1: number;
  bbox_y1: number;
  bbox_x2: number;
  bbox_y2: number;
  vehicle_class: string;
  confidence: number;
  estimated_speed: number;
  color: string;
  plate_text?: string;
  plate_confidence?: number;
}

export interface TrajectoryWaypoint {
  camera_id: string;
  camera_name: string;
  intersection: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  speed_kmh: number;
  plate_confidence: number;
}

export interface Journey {
  journey_id: string;
  global_vehicle_id: string;
  primary_plate?: string;
  vehicle_class?: string;
  color?: string;
  start_camera: string;
  end_camera: string;
  start_time: string;
  end_time: string;
  total_distance_km: number;
  avg_speed_kmh: number;
  trajectory: TrajectoryWaypoint[];
  status: string;
}

export interface TrafficEvent {
  event_id: string;
  event_type: string;
  severity: string;
  camera_id: string;
  timestamp: string;
  details: Record<string, any>;
  resolved: number;
}

export interface WatchlistItem {
  plate_number: string;
  vehicle_desc: string;
  reason: string;
  priority: string;
  added_at: string;
  active: number;
}

export interface NetworkAnalytics {
  online_cameras: number;
  total_active_vehicles: number;
  network_average_speed: number;
  network_total_flow_vph: number;
  hourly_trends: Array<{
    hour: string;
    flow: number;
    avg_speed: number;
    congestion_pct: number;
  }>;
  camera_summaries: CameraMetrics[];
}

export interface GroundedAssistantResponse {
  grounded: boolean;
  answer: string;
  data: any;
  citations: string[];
}

export interface SystemHealth {
  status: string;
  uptime_seconds: number;
  database_size_kb: number;
  total_cameras: number;
  online_cameras: number;
  active_fps: number;
  average_inference_latency_ms: number;
  cuda_available: boolean;
  memory_usage_mb: number;
  cpu_utilization_pct: number;
}

export interface EChallan {
  challan_no: string;
  plate_number: string;
  violation_type: string;
  section_act: string;
  fine_amount: number;
  camera_id: string;
  intersection: string;
  recorded_speed: number;
  speed_limit: number;
  timestamp: string;
  status: 'PENDING_PAYMENT' | 'PAID' | 'DISPUTED';
  officer_badge: string;
  evidence_notes: string;
}

export interface GreenCorridor {
  corridor_id: string;
  name: string;
  emergency_type: string;
  vehicle_plate: string;
  origin_cam: string;
  dest_cam: string;
  route: string[];
  status: string;
  activated_at: string;
  priority_level: string;
}

export interface PcrUnit {
  unit_id: string;
  call_sign: string;
  officer_in_charge: string;
  current_junction: string;
  latitude: number;
  longitude: number;
  status: string;
  last_update: string;
}

