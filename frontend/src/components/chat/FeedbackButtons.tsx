import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { submitFeedback } from "@/lib/api";
import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/lib/utils";

interface FeedbackButtonsProps {
  sessionId: string;
  query:     string;
  response:  string;
}

type State = "idle" | "loading" | "done";

export function FeedbackButtons({ sessionId, query, response }: FeedbackButtonsProps) {
  const [state,  setState]  = useState<State>("idle");
  const [rating, setRating] = useState<1 | -1 | null>(null);

  const submit = async (r: 1 | -1) => {
    if (state !== "idle") return;
    setState("loading");
    setRating(r);
    try {
      await submitFeedback({ session_id: sessionId, query, response, rating: r });
      setState("done");
    } catch {
      setState("idle");
      setRating(null);
    }
  };

  if (state === "done") {
    return (
      <span className="text-xs text-gray-400 dark:text-gray-500 animate-fade-in">
        {rating === 1 ? "Glad it helped!" : "Thanks for the feedback."}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <Tooltip text="Helpful">
        <button
          onClick={() => submit(1)}
          disabled={state === "loading"}
          className={cn(
            "p-1.5 rounded-lg transition-colors",
            rating === 1
              ? "text-green-600 bg-green-50 dark:bg-green-900/20"
              : "text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20",
          )}
        >
          <ThumbsUp size={13} />
        </button>
      </Tooltip>
      <Tooltip text="Not helpful">
        <button
          onClick={() => submit(-1)}
          disabled={state === "loading"}
          className={cn(
            "p-1.5 rounded-lg transition-colors",
            rating === -1
              ? "text-red-500 bg-red-50 dark:bg-red-900/20"
              : "text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20",
          )}
        >
          <ThumbsDown size={13} />
        </button>
      </Tooltip>
    </div>
  );
}