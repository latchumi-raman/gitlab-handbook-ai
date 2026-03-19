export interface Message {
  id:         string;
  role:       "user" | "assistant";
  content:    string;
  sources?:   SourceChunk[];
  confidence?: number;
  followUps?: string[];
  guardrailTriggered?: boolean;
  queryEnhanced?:      boolean;
  originalQuery?:      string;
  timestamp:  Date;
  isStreaming?: boolean;
}

export interface SourceChunk {
  id:            number;
  content:       string;
  source_url:    string;
  page_type:     "handbook" | "direction";
  page_title:    string;
  section_title: string;
  similarity:    number;
}

export type PageTypeFilter = "handbook" | "direction" | "both";

export interface ChatRequest {
  query:             string;
  session_id:        string;
  history:           { role: string; content: string }[];
  page_type_filter?: PageTypeFilter;
  match_count?:      number;
}

export type SSEEvent =
  | { type: "token";          content: string }
  | { type: "sources";        sources: SourceChunk[] }
  | { type: "metadata";       confidence: number; follow_ups: string[]; session_id: string }
  | { type: "guardrail";      triggered: boolean; reason: string }
  | { type: "query_enhanced"; original: string; enhanced: string; message: string }
  | { type: "error";          message: string }
  | { type: "done" };

export interface ChatSession {
  id:        string;
  title:     string;
  messages:  Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface FeedbackPayload {
  session_id: string;
  query:      string;
  response:   string;
  rating:     1 | -1;
  comment?:   string;
}

export interface HealthStatus {
  status:         string;
  version:        string;
  db_connected:   boolean;
  chunks_indexed: number;
}

export type ChatStatus = "idle" | "generating" | "error";

// ── Analytics types ───────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  total_queries:       number;
  queries_last_7_days: number;
  avg_confidence:      number;
  guardrail_rate:      number;
  positive_feedback:   number;
  negative_feedback:   number;
  total_feedback:      number;
  chunks_indexed:      number;
  handbook_chunks:     number;
  direction_chunks:    number;
  queries_per_day:     QueryPerDay[];
  top_queries:         TopQuery[];
}

export interface QueryPerDay {
  day:              string;
  total_queries:    number;
  blocked_queries:  number;
  avg_confidence:   number;
  avg_response_ms:  number;
}

export interface TopQuery {
  normalized_query: string;
  frequency:        number;
  avg_confidence:   number;
}

export interface ConfidenceBucket {
  range: string;
  count: number;
}