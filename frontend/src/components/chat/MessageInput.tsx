import { useRef, useEffect, KeyboardEvent } from "react";
import { Send, Square, Filter } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { Button }       from "@/components/ui/Button";
import { cn }           from "@/lib/utils";
import type { PageTypeFilter } from "@/types";

interface MessageInputProps {
  onSend:        (q: string) => void;
  onStop:        () => void;
  isGenerating:  boolean;
  value:         string;
  onChange:      (v: string) => void;
}

export function MessageInput({ onSend, onStop, isGenerating, value, onChange }: MessageInputProps) {
  const textareaRef   = useRef<HTMLTextAreaElement>(null);
  const pageFilter    = useChatStore((s) => s.pageTypeFilter);
  const setPageFilter = useChatStore((s) => s.setPageFilter);

  // Auto-grow textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [value]);

  // Focus on mount
  useEffect(() => { textareaRef.current?.focus(); }, []);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!value.trim() || isGenerating) return;
    onSend(value.trim());
    onChange("");
    textareaRef.current?.focus();
  };

  const filterOptions: { value: PageTypeFilter; label: string }[] = [
    { value: "both",      label: "All sources" },
    { value: "handbook",  label: "Handbook only" },
    { value: "direction", label: "Direction only" },
  ];

  return (
    <div className="border-t border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-950 px-4 py-3">
      {/* Filter row */}
      <div className="flex items-center gap-1.5 mb-2">
        <Filter size={11} className="text-gray-400 shrink-0" />
        <div className="flex gap-1">
          {filterOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPageFilter(opt.value)}
              className={cn(
                "px-2 py-0.5 rounded-md text-xs transition-colors",
                pageFilter === opt.value
                  ? "bg-orange-100 dark:bg-orange-900/30 text-gitlab-orange dark:text-orange-400 font-medium"
                  : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input row */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about the GitLab handbook...  ⌘ + Enter to send"
            rows={1}
            disabled={isGenerating}
            className={cn(
              "input-base resize-none min-h-[44px] pr-2",
              "disabled:opacity-60 disabled:cursor-not-allowed",
            )}
          />
        </div>

        {isGenerating ? (
          <Button
            variant="danger"
            onClick={onStop}
            className="shrink-0 h-11 w-11 p-0 rounded-xl bg-red-50 dark:bg-red-900/20 hover:bg-red-100"
            title="Stop generation"
          >
            <Square size={15} className="text-red-500 fill-red-500" />
          </Button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim()}
            className="shrink-0 h-11 w-11 rounded-xl
                       bg-gitlab-orange hover:bg-gitlab-red
                       disabled:opacity-40 disabled:cursor-not-allowed
                       flex items-center justify-center
                       transition-colors duration-150"
            title="Send (⌘ + Enter)"
          >
            <Send size={15} className="text-white" />
          </button>
        )}
      </div>
    </div>
  );
}