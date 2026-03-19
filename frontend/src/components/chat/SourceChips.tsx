import { ExternalLink } from "lucide-react";
import type { SourceChunk } from "@/types";
import { formatSourceUrl } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface SourceChipsProps {
  sources:         SourceChunk[];
  onShowDrawer?:   () => void;
  expandedDrawer?: boolean;
}

export function SourceChips({ sources, onShowDrawer, expandedDrawer }: SourceChipsProps) {
  if (!sources.length) return null;

  return (
    <div className="mt-3">
      <p className="text-xs text-gray-400 dark:text-gray-500 mb-1.5">Sources</p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((src) => (
          <a
            key={src.id}
            href={src.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "chip border-surface-200 dark:border-surface-700",
              "bg-surface-50 dark:bg-surface-900",
              "text-gray-600 dark:text-gray-400",
              "hover:border-gitlab-orange/60 hover:text-gitlab-orange",
              "dark:hover:border-gitlab-orange/40 dark:hover:text-orange-400",
            )}
            title={`${src.page_title} — ${src.section_title}`}
          >
            <span className={cn(
              "w-1.5 h-1.5 rounded-full shrink-0",
              src.page_type === "handbook" ? "bg-gitlab-orange" : "bg-gitlab-purple",
            )} />
            {formatSourceUrl(src.source_url)}
            <ExternalLink size={10} className="shrink-0 opacity-50" />
          </a>
        ))}

        {onShowDrawer && (
          <button
            onClick={onShowDrawer}
            className={cn(
              "chip border-dashed transition-colors",
              expandedDrawer
                ? "border-gitlab-orange text-gitlab-orange bg-orange-50 dark:bg-orange-900/10"
                : "border-surface-300 dark:border-surface-600 text-gray-500 dark:text-gray-400 hover:border-gitlab-orange hover:text-gitlab-orange",
            )}
          >
            {expandedDrawer ? "Hide chunks" : "Show raw chunks"}
          </button>
        )}
      </div>
    </div>
  );
}