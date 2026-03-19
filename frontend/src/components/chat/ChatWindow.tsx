import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { MessageInput }  from "./MessageInput";
import { useChat }       from "@/hooks/useChat";
import { useChatStore }  from "@/store/chatStore";
import { Sparkles }      from "lucide-react";

const WELCOME_PROMPTS = [
  "What are GitLab's CREDIT values?",
  "How does GitLab handle all-remote work?",
  "What is GitLab's hiring process?",
  "How do GitLab's engineering teams run OKRs?",
  "What does the iteration value mean in practice?",
  "How does GitLab handle performance reviews?",
];

export function ChatWindow() {
  const { sendChat, stopGeneration, isGenerating } = useChat();
  const messages = useChatStore((s) => s.activeMessages());
  const bottomRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");

  // Auto-scroll to bottom on new messages / tokens
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Keyboard shortcut: Cmd+K focuses the input
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        document.querySelector<HTMLTextAreaElement>("textarea")?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleSend = (query: string) => {
    setInput("");
    sendChat(query);
  };

  const handleFollowUp = (q: string) => {
    setInput(q);
    setTimeout(() => handleSend(q), 50);
  };

  // ── Empty state ───────────────────────────────────────────────────────────
  if (messages.length === 0) {
    return (
      <div className="flex flex-col flex-1 min-h-0">
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
          {/* Logo / brand */}
          <div className="w-14 h-14 rounded-2xl
                          bg-gradient-to-br from-gitlab-orange to-gitlab-red
                          flex items-center justify-center mb-5 shadow-sm">
            <Sparkles size={26} className="text-white" />
          </div>
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-1">
            GitLab Handbook AI
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-8 max-w-sm">
            Ask anything about GitLab's handbook, values, processes, and company direction.
          </p>

          {/* Prompt suggestions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
            {WELCOME_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => handleSend(p)}
                className="text-left px-4 py-3 rounded-xl text-sm
                           border border-surface-200 dark:border-surface-700
                           bg-white dark:bg-surface-900
                           text-gray-700 dark:text-gray-300
                           hover:border-gitlab-orange/60 hover:text-gitlab-orange
                           dark:hover:border-gitlab-orange/40
                           transition-colors duration-150"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <MessageInput
          onSend={handleSend}
          onStop={stopGeneration}
          isGenerating={isGenerating}
          value={input}
          onChange={setInput}
        />
      </div>
    );
  }

  // ── Chat with messages ────────────────────────────────────────────────────
  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.map((msg, idx) => {
          // Find the preceding user message for feedback attribution
          const prevUser =
            msg.role === "assistant"
              ? messages.slice(0, idx).reverse().find((m) => m.role === "user")?.content
              : undefined;

          return (
            <MessageBubble
              key={msg.id}
              message={msg}
              prevUserMsg={prevUser}
              onFollowUp={handleFollowUp}
            />
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSend}
        onStop={stopGeneration}
        isGenerating={isGenerating}
        value={input}
        onChange={setInput}
      />
    </div>
  );
}