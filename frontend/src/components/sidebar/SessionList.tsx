import { Trash2 } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

export function SessionList() {
  const sessions        = useChatStore((s) => s.sessions);
  const activeId        = useChatStore((s) => s.activeSessionId);
  const switchSession   = useChatStore((s) => s.switchSession);
  const deleteSession   = useChatStore((s) => s.deleteSession);

  const recentSessions = sessions.slice(0, 12);

  if (recentSessions.length === 0) return null;

  return (
    <div>
      <p className="px-3 text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1.5">
        Recent chats
      </p>
      {recentSessions.map((s) => (
        <div
          key={s.id}
          className={cn(
            "sidebar-item group",
            s.id === activeId && "active",
          )}
        >
          <button
            className="flex-1 text-left truncate"
            onClick={() => switchSession(s.id)}
          >
            <span className="block truncate text-sm">{s.title}</span>
            <span className="block text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              {formatDistanceToNow(new Date(s.updatedAt), { addSuffix: true })}
            </span>
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:text-red-400 transition"
            title="Delete chat"
          >
            <Trash2 size={12} />
          </button>
        </div>
      ))}
    </div>
  );
}