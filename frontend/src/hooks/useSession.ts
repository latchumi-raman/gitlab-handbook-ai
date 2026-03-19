
import { useChatStore } from "@/store/chatStore";
import { clearServerSession } from "@/lib/api";

export function useSession() {
  const activeSessionId  = useChatStore((s) => s.activeSessionId);
  const newSessionAction = useChatStore((s) => s.newSession);

  const startNewChat = async () => {
    // Clear server-side memory for this session
    try { await clearServerSession(activeSessionId); } catch { /* best-effort */ }
    newSessionAction();
  };

  return { sessionId: activeSessionId, startNewChat };
}