import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { FeedbackButtons } from "@/components/chat/FeedbackButtons";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  submitFeedback: vi.fn(),
}));

const defaultProps = {
  sessionId: "test-session-123",
  query:     "What are GitLab values?",
  response:  "GitLab values are CREDIT...",
};

describe("FeedbackButtons", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders thumbs up and thumbs down buttons", () => {
    render(<FeedbackButtons {...defaultProps} />);
    expect(screen.getByTitle(/helpful/i)).toBeTruthy();
    expect(screen.getByTitle(/not helpful/i)).toBeTruthy();
  });

  it("calls submitFeedback with rating 1 on thumbs up click", async () => {
    vi.mocked(api.submitFeedback).mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByTitle(/^helpful$/i));

    await waitFor(() => {
      expect(api.submitFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          session_id: "test-session-123",
          rating:     1,
        }),
      );
    });
  });

  it("calls submitFeedback with rating -1 on thumbs down click", async () => {
    vi.mocked(api.submitFeedback).mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByTitle(/not helpful/i));

    await waitFor(() => {
      expect(api.submitFeedback).toHaveBeenCalledWith(
        expect.objectContaining({ rating: -1 }),
      );
    });
  });

  it("shows thank you message after positive feedback", async () => {
    vi.mocked(api.submitFeedback).mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByTitle(/^helpful$/i));

    await waitFor(() => {
      expect(screen.getByText(/glad it helped/i)).toBeTruthy();
    });
  });

  it("shows thank you message after negative feedback", async () => {
    vi.mocked(api.submitFeedback).mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByTitle(/not helpful/i));

    await waitFor(() => {
      expect(screen.getByText(/thanks for the feedback/i)).toBeTruthy();
    });
  });

  it("buttons disabled after submission", async () => {
    vi.mocked(api.submitFeedback).mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByTitle(/^helpful$/i));

    // After submission, the buttons disappear and a thank-you msg appears
    await waitFor(() => {
      expect(screen.queryByTitle(/^helpful$/i)).toBeNull();
    });
  });

  it("recovers gracefully if API call fails", async () => {
    vi.mocked(api.submitFeedback).mockRejectedValue(new Error("Network error"));
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByTitle(/^helpful$/i));

    // Should reset to idle state — buttons visible again
    await waitFor(() => {
      expect(screen.getByTitle(/^helpful$/i)).toBeTruthy();
    });
  });
});