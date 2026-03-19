import { describe, it, expect, vi } from "vitest";
import {
  truncate,
  formatSourceUrl,
  formatConfidence,
  confidenceColor,
  confidenceBarColor,
  exportAsMarkdown,
} from "@/lib/utils";
import type { Message } from "@/types";

// ── truncate ──────────────────────────────────────────────────────────────────

describe("truncate", () => {
  it("returns string unchanged if shorter than maxLen", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("truncates and adds ellipsis if longer than maxLen", () => {
    const result = truncate("hello world", 8);
    expect(result.length).toBe(8);
    expect(result.endsWith("…")).toBe(true);
  });

  it("returns string unchanged when exactly maxLen", () => {
    expect(truncate("hello", 5)).toBe("hello");
  });

  it("handles empty string", () => {
    expect(truncate("", 10)).toBe("");
  });
});

// ── formatSourceUrl ───────────────────────────────────────────────────────────

describe("formatSourceUrl", () => {
  it("formats valid handbook URL", () => {
    const result = formatSourceUrl("https://handbook.gitlab.com/handbook/values/");
    expect(result).toContain("handbook.gitlab.com");
  });

  it("replaces hyphens with spaces in path segment", () => {
    const result = formatSourceUrl("https://handbook.gitlab.com/all-remote-work/");
    expect(result).toContain("all remote work");
  });

  it("returns original URL if invalid", () => {
    expect(formatSourceUrl("not-a-url")).toBe("not-a-url");
  });

  it("handles URL with no path", () => {
    const result = formatSourceUrl("https://handbook.gitlab.com/");
    expect(result).toContain("handbook.gitlab.com");
  });
});

// ── formatConfidence ──────────────────────────────────────────────────────────

describe("formatConfidence", () => {
  it("formats 0.87 as 87%", () => {
    expect(formatConfidence(0.87)).toBe("87%");
  });

  it("formats 1.0 as 100%", () => {
    expect(formatConfidence(1.0)).toBe("100%");
  });

  it("formats 0.0 as 0%", () => {
    expect(formatConfidence(0.0)).toBe("0%");
  });

  it("rounds correctly — 0.876 → 88%", () => {
    expect(formatConfidence(0.876)).toBe("88%");
  });

  it("rounds down correctly — 0.874 → 87%", () => {
    expect(formatConfidence(0.874)).toBe("87%");
  });
});

// ── confidenceColor ───────────────────────────────────────────────────────────

describe("confidenceColor", () => {
  it("returns green class for score >= 0.80", () => {
    expect(confidenceColor(0.85)).toContain("green");
    expect(confidenceColor(0.80)).toContain("green");
  });

  it("returns amber class for score 0.60–0.79", () => {
    expect(confidenceColor(0.70)).toContain("amber");
    expect(confidenceColor(0.60)).toContain("amber");
  });

  it("returns red class for score < 0.60", () => {
    expect(confidenceColor(0.59)).toContain("red");
    expect(confidenceColor(0.0)).toContain("red");
  });
});

// ── confidenceBarColor ────────────────────────────────────────────────────────

describe("confidenceBarColor", () => {
  it("returns green bg class for high confidence", () => {
    expect(confidenceBarColor(0.90)).toBe("bg-green-500");
  });

  it("returns amber bg class for medium confidence", () => {
    expect(confidenceBarColor(0.70)).toBe("bg-amber-500");
  });

  it("returns red bg class for low confidence", () => {
    expect(confidenceBarColor(0.40)).toBe("bg-red-500");
  });
});

// ── exportAsMarkdown ──────────────────────────────────────────────────────────

describe("exportAsMarkdown", () => {
  const makeMsg = (role: "user" | "assistant", content: string): Message => ({
    id:        "test-id",
    role,
    content,
    timestamp: new Date(),
  });

  it("triggers file download", () => {
    const createObjURL = vi.fn(() => "blob:mock");
    const revokeObjURL = vi.fn();
    URL.createObjectURL = createObjURL;
    URL.revokeObjectURL = revokeObjURL;

    const clickMock = vi.fn();
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      if (tag === "a") {
        return { href: "", download: "", click: clickMock } as unknown as HTMLAnchorElement;
      }
      return document.createElement(tag);
    });

    exportAsMarkdown([makeMsg("user", "Hello"), makeMsg("assistant", "Hi there")]);
    expect(clickMock).toHaveBeenCalled();
  });
});