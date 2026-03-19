import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import type { SourceChunk } from "@/types";
import { formatSourceUrl, formatConfidence, confidenceColor } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface SourceDrawerProps {
  sources: SourceChunk[];
  open:    boolean;
}

export function SourceDrawer({ sources, open }: SourceDrawerProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!open || !sources.length) return null;

  return (
    <div className="mt-3 rounded-xl border border-surface-200 dark:border-surface-700 overflow-hidden animate-slide-up">
      <div className="px-3 py-2 bg-surface-100 dark:bg-surface-800 flex items-center justify-between">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
          Retrieved context chunks ({sources.length})
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          Used for this answer
        </span>
      </div>

      <div className="divide-y divide-surface-100 dark:divide-surface-800">
        {sources.map((src, idx) => (
          <div key={src.id} className="bg-white dark:bg-surface-900">
            <button
              className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
              onClick={() => setExpanded(expanded === idx ? null : idx)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className={cn(
                  "text-xs font-medium tabular-nums shrink-0",
                  confidenceColor(src.similarity)
                )}>
                  {formatConfidence(src.similarity)}
                </span>
                <span className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0",
                  src.page_type === "handbook" ? "bg-gitlab-orange" : "bg-gitlab-purple"
                )} />
                <span className="text-xs text-gray-600 dark:text-gray-300 truncate">
                  {src.page_title || formatSourceUrl(src.source_url)}
                </span>
                {src.section_title && (
                  <span className="text-xs text-gray-400 dark:text-gray-500 truncate hidden sm:inline">
                    › {src.section_title}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1.5 shrink-0 ml-2">
                <a
                  href={src.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-gray-400 hover:text-gitlab-orange transition-colors"
                >
                  <ExternalLink size={11} />
                </a>
                {expanded === idx
                  ? <ChevronUp  size={13} className="text-gray-400" />
                  : <ChevronDown size={13} className="text-gray-400" />
                }
              </div>
            </button>

            {expanded === idx && (
              <div className="px-3 pb-3 animate-slide-up">
                <pre className="text-xs font-mono text-gray-600 dark:text-gray-300 bg-surface-50 dark:bg-surface-950 rounded-lg p-3 whitespace-pre-wrap overflow-x-auto leading-relaxed max-h-48 overflow-y-auto">
                  {src.content}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}