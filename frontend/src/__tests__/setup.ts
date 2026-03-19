import "@testing-library/jest-dom";
import { vi, beforeEach, afterEach } from "vitest";

// Mock window.matchMedia — not available in jsdom
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches:             false,
    media:               query,
    onchange:            null,
    addListener:         vi.fn(),
    removeListener:      vi.fn(),
    addEventListener:    vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent:       vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem:    (k: string) => store[k] ?? null,
    setItem:    (k: string, v: string) => { store[k] = v; },
    removeItem: (k: string) => { delete store[k]; },
    clear:      () => { store = {}; },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock navigator.clipboard
Object.defineProperty(navigator, "clipboard", {
  writable: true,
  value: { writeText: vi.fn().mockResolvedValue(undefined) },
});

// Suppress console.error for expected test errors
const originalError = console.error.bind(console);
beforeEach(() => {
  vi.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
    const msg = String(args[0]);
    // Allow React warnings through but suppress noisy test errors
    if (msg.includes("Warning: ReactDOM.render") || msg.includes("act(...)")) return;
    originalError(...args);
  });
});
afterEach(() => {
  vi.restoreAllMocks();
});