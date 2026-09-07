export interface PointRule {
  id: number;
  start_time: string;
  end_time: string;
  points: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

// Task: configurable company timezone offset — a fixed numeric UTC offset in
// minutes (NOT a named/DST-aware timezone), used by calculate_points() to
// convert a submission's UTC timestamp before checking it against the
// PointRule windows above. See business_logic_service.py's module docs for
// the full DST-vs-fixed-offset tradeoff this deliberately accepts.
export interface AppSettings {
  company_utc_offset_minutes: number;
  updated_at: string;
}
