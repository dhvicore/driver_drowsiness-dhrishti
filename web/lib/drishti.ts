export const API =
  process.env.NEXT_PUBLIC_DRISHTI_API ?? "";

export type Metrics = {
  face: boolean;
  status: string;
  severity: number;
  attention: string;
  eye_state: string;
  ear: number;
  mar: number;
  closed_duration: number;
  blinks: number;
  perclos: number;
  yawn: boolean;
  yawn_count: number;
  recent_yawns: number;
  recent_long_closures: number;
  evidence_score: number;
  drowsiness_score: number;
  drowsiness_status: string;
  head_direction: string;
  pitch: number;
  yaw: number;
  head_duration: number;
  head_distracted: boolean;
  distraction_score: number;
  phone_detected: boolean;
  phone_using: boolean;
  phone_confidence: number;
  phone_duration: number;
  phone_source: string;
};

export type DrishtiEvent = {
  id: number;
  level: "info" | "warning" | "critical";
  message: string;
  at: number;
};

export type Snapshot = {
  running: boolean;
  error: string | null;
  fps: number;
  raw_overlay: boolean;
  duration: number;
  metrics: Metrics;
  totals: { yawns: number; long_closures: number; blinks: number; phone_events: number };
  events: DrishtiEvent[];
};

export async function getState(signal?: AbortSignal): Promise<Snapshot> {
  const res = await fetch(`${API}/api/state`, { signal, cache: "no-store" });
  if (!res.ok) throw new Error("state unavailable");
  return res.json();
}

export async function post(path: string, body?: unknown) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

export function formatDuration(seconds: number) {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return [h, m, s % 60].map((n) => String(n).padStart(2, "0")).join(":");
}

/** Severity 0 alert · 1 elevated · 2 high · 3 critical */
export function toneFor(severity: number) {
  if (severity >= 3)
    return {
      text: "text-burgundy-on",
      bg: "bg-burgundy",
      border: "border-burgundy",
      dot: "bg-burgundy-on",
      accent: "text-burgundy",
    };
  if (severity === 2)
    return {
      text: "text-burgundy",
      bg: "bg-burgundy-wash",
      border: "border-burgundy",
      dot: "bg-burgundy",
      accent: "text-burgundy",
    };
  if (severity === 1)
    return {
      text: "text-ink",
      bg: "bg-raised",
      border: "border-line-strong",
      dot: "bg-ink-2",
      accent: "text-ink",
    };
  return {
    text: "text-blue",
    bg: "bg-blue-wash",
    border: "border-blue",
    dot: "bg-blue",
    accent: "text-blue",
  };
}
