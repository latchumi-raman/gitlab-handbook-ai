import { formatConfidence, confidenceColor, confidenceBarColor } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  score: number;
}

export function ConfidenceBar({ score }: ConfidenceBarProps) {
  const pct   = Math.round(score * 100);
  const label =
    score >= 0.80 ? "High confidence"
    : score >= 0.60 ? "Medium confidence"
    : "Low confidence — verify sources";

  return (
    <div className="flex items-center gap-2 mt-2">
      <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">Confidence</span>
      <div className="flex-1 h-1.5 rounded-full bg-surface-200 dark:bg-surface-700 overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", confidenceBarColor(score))}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={cn("text-xs font-medium tabular-nums shrink-0", confidenceColor(score))}>
        {formatConfidence(score)}
      </span>
      <span className="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline">
        · {label}
      </span>
    </div>
  );
}