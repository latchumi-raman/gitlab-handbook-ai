import { ArrowRight } from "lucide-react";

interface FollowUpSuggestionsProps {
  suggestions: string[];
  onSelect:    (q: string) => void;
}

export function FollowUpSuggestions({ suggestions, onSelect }: FollowUpSuggestionsProps) {
  if (!suggestions.length) return null;

  return (
    <div className="mt-3">
      <p className="text-xs text-gray-400 dark:text-gray-500 mb-1.5">Suggested follow-ups</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onSelect(s)}
            className="group flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full
                       border border-surface-200 dark:border-surface-700
                       bg-white dark:bg-surface-900
                       text-gray-600 dark:text-gray-300
                       hover:border-gitlab-orange/60 hover:text-gitlab-orange
                       dark:hover:border-gitlab-orange/40 dark:hover:text-orange-400
                       transition-colors"
          >
            {s}
            <ArrowRight size={10} className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        ))}
      </div>
    </div>
  );
}