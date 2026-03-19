import type { TopQuery } from "@/types";
import { formatConfidence, confidenceColor } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface TopQueriesTableProps {
  queries: TopQuery[];
}

export function TopQueriesTable({ queries }: TopQueriesTableProps) {
  if (!queries.length) {
    return (
      <p className="text-sm text-gray-400 py-4 text-center">
        No queries recorded yet
      </p>
    );
  }

  const maxFreq = Math.max(...queries.map((q) => q.frequency));

  return (
    <div className="space-y-2">
      {queries.map((q, i) => (
        <div key={i} className="group">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-700 dark:text-gray-300 truncate max-w-[70%]">
              {q.normalized_query}
            </span>
            <div className="flex items-center gap-3 shrink-0">
              <span className={cn("text-xs font-medium", confidenceColor(q.avg_confidence))}>
                {formatConfidence(q.avg_confidence)} avg
              </span>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 tabular-nums">
                {q.frequency}×
              </span>
            </div>
          </div>
          <div className="h-1 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gitlab-orange/60 rounded-full transition-all duration-500"
              style={{ width: `${(q.frequency / maxFreq) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}