import { create } from "zustand";
import { persist } from "zustand/middleware";
import { v4 as uuidv4 } from "uuid";
import type { Message, ChatSession, PageTypeFilter, ChatStatus } from "@/types";

interface ChatState {
  // Active session
  activeSessionId: string;
  sessions:        ChatSession[];
  status:          ChatStatus;
  sidebarOpen:     boolean;

  // Settings
  pageTypeFilter:  PageTypeFilter;
  matchCount:      number;

  // Derived
  activeSession:   () => ChatSession | undefined;
  activeMessages:  () => Message[];

  // Actions
  sendMessage:     () => string;  // returns temp msg id
  appendToken:     (msgId: string, token: string) => void;
  finalizeMessage: (msgId: string, updates: Partial<Message>) => void;
  addUserMessage:  (content: string) => Message;
  newSession:      () => void;
  switchSession:   (id: string) => void;
  deleteSession:   (id: string) => void;
  setStatus:       (status: ChatStatus) => void;
  toggleSidebar:   () => void;
  setPageFilter:   (f: PageTypeFilter) => void;
}

const newSession = (): ChatSession => ({
  id:        uuidv4(),
  title:     "New conversation",
  messages:  [],
  createdAt: new Date(),
  updatedAt: new Date(),
});

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      activeSessionId: uuidv4(),
      sessions:        [newSession()],
      status:          "idle",
      sidebarOpen:     true,
      pageTypeFilter:  "both",
      matchCount:      5,

      activeSession: () =>
        get().sessions.find((s) => s.id === get().activeSessionId),

      activeMessages: () =>
        get().activeSession()?.messages ?? [],

      // Add user message immediately (optimistic)
      addUserMessage: (content) => {
        const msg: Message = {
          id:        uuidv4(),
          role:      "user",
          content,
          timestamp: new Date(),
        };
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id !== state.activeSessionId
              ? s
              : {
                  ...s,
                  messages:  [...s.messages, msg],
                  title:     s.messages.length === 0 ? content.slice(0, 42) : s.title,
                  updatedAt: new Date(),
                },
          ),
        }));
        return msg;
      },

      // Add empty assistant message placeholder (will be filled by streaming)
      sendMessage: () => {
        const msgId = uuidv4();
        const placeholder: Message = {
          id:         msgId,
          role:       "assistant",
          content:    "",
          timestamp:  new Date(),
          isStreaming: true,
        };
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id !== state.activeSessionId
              ? s
              : { ...s, messages: [...s.messages, placeholder], updatedAt: new Date() },
          ),
        }));
        return msgId;
      },

      // Append a streaming token to a message
      appendToken: (msgId, token) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id !== state.activeSessionId
              ? s
              : {
                  ...s,
                  messages: s.messages.map((m) =>
                    m.id !== msgId ? m : { ...m, content: m.content + token },
                  ),
                },
          ),
        }));
      },

      // Mark streaming done and attach metadata
      finalizeMessage: (msgId, updates) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id !== state.activeSessionId
              ? s
              : {
                  ...s,
                  messages: s.messages.map((m) =>
                    m.id !== msgId
                      ? m
                      : { ...m, ...updates, isStreaming: false },
                  ),
                },
          ),
        }));
      },

      newSession: () => {
        const session = newSession();
        set((state) => ({
          sessions:        [session, ...state.sessions].slice(0, 20), // keep last 20
          activeSessionId: session.id,
          status:          "idle",
        }));
      },

      switchSession: (id) => {
        set({ activeSessionId: id, status: "idle" });
      },

      deleteSession: (id) => {
        set((state) => {
          const remaining = state.sessions.filter((s) => s.id !== id);
          if (remaining.length === 0) {
            const fresh = newSession();
            return { sessions: [fresh], activeSessionId: fresh.id };
          }
          const newActive =
            state.activeSessionId === id ? remaining[0].id : state.activeSessionId;
          return { sessions: remaining, activeSessionId: newActive };
        });
      },

      setStatus: (status) => set({ status }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setPageFilter: (pageTypeFilter) => set({ pageTypeFilter }),
    }),
    {
      name:    "gitlab-ai-chat",
      partialize: (state) => ({
        sessions:        state.sessions,
        activeSessionId: state.activeSessionId,
        pageTypeFilter:  state.pageTypeFilter,
        sidebarOpen:     state.sidebarOpen,
      }),
    },
  ),
);