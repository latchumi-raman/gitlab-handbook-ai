import { useEffect } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface KeyboardShortcutsModalProps {
  open:    boolean;
  onClose: () => void;
}

const SHORTCUTS = [
  { keys: ["⌘", "K"],     description: "Focus chat input" },
  { keys: ["⌘", "↵"],     description: "Send message" },
  { keys: ["⌘", "⇧", "N"], description: "New conversation" },
  { keys: ["⌘", "\\"],    description: "Toggle sidebar" },
  { keys: ["⌘", "D"],     description: "Toggle dark mode" },
  { keys: ["⌘", "E"],     description: "Export as markdown" },
  { keys: ["⌘", "⇧", "E"], description: "Export as PDF" },
  { keys: ["Esc"],         description: "Stop generation" },
  { keys: ["?"],           description: "Show this dialog" },
];

export function KeyboardShortcutsModal({ open, onClose }: KeyboardShortcutsModalProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-700
                   w-full max-w-sm mx-4 p-5 shadow-xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-800 dark:text-gray-100">Keyboard shortcuts</h2>
          <button onClick={onClose} className="btn-ghost p-1">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-2">
          {SHORTCUTS.map(({ keys, description }) => (
            <div key={description} className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">{description}</span>
              <div className="flex items-center gap-1">
                {keys.map((k, i) => (
                  <span key={i} className={cn(
                    "inline-flex items-center justify-center min-w-[26px] h-6 px-1.5",
                    "rounded-md border border-surface-200 dark:border-surface-700",
                    "bg-surface-50 dark:bg-surface-800",
                    "text-xs font-mono font-medium text-gray-600 dark:text-gray-300",
                  )}>
                    {k}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}