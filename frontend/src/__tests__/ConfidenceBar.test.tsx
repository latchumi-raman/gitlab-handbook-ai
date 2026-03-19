import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ConfidenceBar } from "@/components/chat/ConfidenceBar";

describe("ConfidenceBar", () => {
  it("renders without crashing", () => {
    render(<ConfidenceBar score={0.85} />);
    expect(screen.getByText(/confidence/i)).toBeTruthy();
  });

  it("displays correct percentage for 0.87", () => {
    render(<ConfidenceBar score={0.87} />);
    expect(screen.getByText("87%")).toBeTruthy();
  });

  it("displays 100% for perfect score", () => {
    render(<ConfidenceBar score={1.0} />);
    expect(screen.getByText("100%")).toBeTruthy();
  });

  it("displays 0% for zero score", () => {
    render(<ConfidenceBar score={0.0} />);
    expect(screen.getByText("0%")).toBeTruthy();
  });

  it("shows high confidence label for score >= 0.80", () => {
    render(<ConfidenceBar score={0.92} />);
    expect(screen.getByText(/high confidence/i)).toBeTruthy();
  });

  it("shows medium confidence label for score 0.60–0.79", () => {
    render(<ConfidenceBar score={0.72} />);
    expect(screen.getByText(/medium confidence/i)).toBeTruthy();
  });

  it("shows low confidence label for score < 0.60", () => {
    render(<ConfidenceBar score={0.40} />);
    expect(screen.getByText(/low confidence/i)).toBeTruthy();
  });

  it("progress bar width matches score percentage", () => {
    const { container } = render(<ConfidenceBar score={0.65} />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar).toBeTruthy();
    expect(bar.style.width).toBe("65%");
  });
});