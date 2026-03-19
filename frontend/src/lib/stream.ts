import type { SSEEvent } from "@/types";

/**
 * Read a Server-Sent Events stream from a POST endpoint.
 * The browser's native EventSource only supports GET, so we use
 * fetch + ReadableStream instead.
 *
 * Calls onEvent for each parsed SSE event object.
 * Calls onError if the stream fails.
 */
export async function readSSEStream(
  url:     string,
  body:    object,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    throw new Error(`Stream request failed: HTTP ${res.status}`);
  }
  if (!res.body) {
    throw new Error("Response body is null — SSE not supported");
  }

  const reader  = res.body.getReader();
  const decoder = new TextDecoder();
  let   buffer  = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by double newlines
      const parts = buffer.split("\n\n");
      // Keep the last (potentially incomplete) chunk in the buffer
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data: ")) continue;

        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr) as SSEEvent;
          onEvent(event);
        } catch {
          // Malformed JSON — skip
          console.warn("SSE parse error:", jsonStr);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}