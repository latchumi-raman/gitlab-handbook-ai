import { SquarePen } from "lucide-react";
import { QuickTopics }  from "./QuickTopics";
import { SessionList }  from "./SessionList";
import { useSession }   from "@/hooks/useSession";
import { useChatStore } from "@/store/chatStore";
import { cn }           from "@/lib/utils";

interface SidebarProps {
  onTopicSelect: (q: string) => void;
}

export function Sidebar({ onTopicSelect }: SidebarProps) {
  const { startNewChat } = useSession();
  const sidebarOpen      = useChatStore((s) => s.sidebarOpen);

  return (
    <aside className={cn(
      "flex-col border-r border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-950",
      "transition-all duration-200 overflow-hidden",
      sidebarOpen ? "flex w-56" : "hidden",
    )}>
      {/* Top */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-surface-100 dark:border-surface-800">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-gitlab-orange to-gitlab-red flex items-center justify-center">
            <span className="text-white font-bold text-xs">GL</span>
          </div>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">
            Handbook AI
          </span>
        </div>
        <button
          onClick={startNewChat}
          className="p-1.5 rounded-lg text-gray-400 hover:text-gitlab-orange hover:bg-orange-50 dark:hover:bg-orange-900/10 transition-colors"
          title="New chat"
        >
          <SquarePen size={15} />
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto py-3 px-1 space-y-5">
        <QuickTopics onSelect={onTopicSelect} />
        <SessionList />
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-surface-100 dark:border-surface-800">
        <p className="text-xs text-gray-400 dark:text-gray-500 text-center">
          Powered by Gemini 2.5 Flash
        </p>
      </div>
    </aside>
  );
}