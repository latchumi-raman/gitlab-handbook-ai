import type { FeedbackPayload, HealthStatus, AnalyticsSummary, ConfidenceBucket } from "@/types";

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export const endpoints = {
  chatStream:           `${API_BASE}/api/v1/chat/stream`,
  chat:                 `${API_BASE}/api/v1/chat`,
  feedback:             `${API_BASE}/api/v1/feedback`,
  health:               `${API_BASE}/api/v1/health`,
  ping:                 `${API_BASE}/api/v1/ping`,
  stats:                `${API_BASE}/api/v1/stats`,
  session:              (id: string) => `${API_BASE}/api/v1/session/${id}`,
  analyticsSummary:     `${API_BASE}/api/v1/analytics/summary`,
  analyticsConfidence:  `${API_BASE}/api/v1/analytics/confidence`,
  analyticsFeedback:    `${API_BASE}/api/v1/analytics/feedback`,
};

export async function submitFeedback(payload: FeedbackPayload): Promise<void> {
  const res = await fetch(endpoints.feedback, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Feedback API error ${res.status}`);
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(endpoints.health);
  if (!res.ok) throw new Error(`Health check failed ${res.status}`);
  return res.json();
}

export async function fetchStats(): Promise<{ totals: Record<string, number>; grand_total: number }> {
  const res = await fetch(endpoints.stats);
  if (!res.ok) throw new Error(`Stats failed ${res.status}`);
  return res.json();
}

export async function clearServerSession(sessionId: string): Promise<void> {
  await fetch(endpoints.session(sessionId), { method: "DELETE" });
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const res = await fetch(endpoints.analyticsSummary);
  if (!res.ok) throw new Error(`Analytics summary failed ${res.status}`);
  const json = await res.json();
  return json.data as AnalyticsSummary;
}

export async function fetchConfidenceDistribution(): Promise<ConfidenceBucket[]> {
  const res = await fetch(endpoints.analyticsConfidence);
  if (!res.ok) throw new Error(`Confidence distribution failed ${res.status}`);
  const json = await res.json();
  return json.data as ConfidenceBucket[];
}