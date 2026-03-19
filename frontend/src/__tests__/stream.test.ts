import { describe, it, expect, vi, beforeEach } from "vitest";
import { readSSEStream } from "@/lib/stream";

// Build a fake ReadableStream from a raw SSE string
function makeSSEStream(raw: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const bytes   = encoder.encode(raw);
  return new ReadableStream({
    start(controller) {
      controller.enqueue(bytes);
      controller.close();
    },
  });
}

function makeFetchMock(raw: string, status = 200) {
  return vi.fn().mockResolvedValue({
    ok:     status < 400,
    status,
    body:   makeSSEStream(raw),
  });
}

describe("readSSEStream", () => {
  const sseBody = [
    `data: {"type":"token","content":"Hello "}\n\n`,
    `data: {"type":"token","content":"world!"}\n\n`,
    `data: {"type":"sources","sources":[]}\n\n`,
    `data: {"type":"done"}\n\n`,
  ].join("");

  beforeEach(() => {
    vi.stubGlobal("fetch", makeFetchMock(sseBody));
  });

  it("calls onEvent for each parsed SSE event", async () => {
    const events: unknown[] = [];
    await readSSEStream(
      "http://localhost:8000/api/v1/chat/stream",
      { query: "test", session_id: "s1", history: [] },
      (evt) => events.push(evt),
    );
    expect(events.length).toBe(4);
  });

  it("passes correct event types to onEvent", async () => {
    const types: string[] = [];
    await readSSEStream(
      "http://localhost:8000/api/v1/chat/stream",
      { query: "test", session_id: "s1", history: [] },
      (evt) => types.push((evt as { type: string }).type),
    );
    expect(types).toContain("token");
    expect(types).toContain("sources");
    expect(types).toContain("done");
  });

  it("reconstructs token content correctly", async () => {
    const tokens: string[] = [];
    await readSSEStream(
      "http://localhost:8000/api/v1/chat/stream",
      { query: "test", session_id: "s1", history: [] },
      (evt) => {
        if ((evt as { type: string }).type === "token") {
          tokens.push((evt as { type: string; content: string }).content);
        }
      },
    );
    expect(tokens.join("")).toBe("Hello world!");
  });

  it("throws on non-200 response", async () => {
    vi.stubGlobal("fetch", makeFetchMock("", 503));
    await expect(
      readSSEStream("http://test", {}, vi.fn()),
    ).rejects.toThrow("503");
  });

  it("skips malformed SSE lines without crashing", async () => {
    const badSSE = [
      `data: {"type":"token","content":"ok"}\n\n`,
      `data: NOT_VALID_JSON\n\n`,
      `data: {"type":"done"}\n\n`,
    ].join("");
    vi.stubGlobal("fetch", makeFetchMock(badSSE));

    const events: unknown[] = [];
    await expect(
      readSSEStream("http://test", {}, (e) => events.push(e)),
    ).resolves.not.toThrow();

    // Should have processed the 2 valid events, skipped the bad one
    expect(events.length).toBe(2);
  });

  it("respects AbortSignal cancellation", async () => {
    const controller = new AbortController();
    controller.abort();   // abort immediately

    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(
      Object.assign(new Error("AbortError"), { name: "AbortError" }),
    ));

    await expect(
      readSSEStream("http://test", {}, vi.fn(), controller.signal),
    ).rejects.toThrow("AbortError");
  });
});