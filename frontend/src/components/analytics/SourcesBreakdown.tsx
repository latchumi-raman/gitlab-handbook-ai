interface SourcesBreakdownProps {
  handbookChunks:  number;
  directionChunks: number;
  total:           number;
}

export function SourcesBreakdown({ handbookChunks, directionChunks, total }: SourcesBreakdownProps) {
  const handbookPct  = total ? Math.round((handbookChunks  / total) * 100) : 0;
  const directionPct = total ? Math.round((directionChunks / total) * 100) : 0;

  return (
    <div className="space-y-3">
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-600 dark:text-gray-300 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-gitlab-orange inline-block" />
            Handbook
          </span>
          <span className="font-medium text-gray-700 dark:text-gray-200 tabular-nums">
            {handbookChunks.toLocaleString()} ({handbookPct}%)
          </span>
        </div>
        <div className="h-2 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gitlab-orange rounded-full transition-all duration-700"
            style={{ width: `${handbookPct}%` }}
          />
        </div>
      </div>

      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-600 dark:text-gray-300 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-gitlab-purple inline-block" />
            Direction
          </span>
          <span className="font-medium text-gray-700 dark:text-gray-200 tabular-nums">
            {directionChunks.toLocaleString()} ({directionPct}%)
          </span>
        </div>
        <div className="h-2 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gitlab-purple rounded-full transition-all duration-700"
            style={{ width: `${directionPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}